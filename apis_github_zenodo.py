"""
Enrich the VoR `mir-datasets.yaml` file with API-retrieved information.

1.
Open the `mir-datasets.yaml` file
which is structured as a mapping of
dataset name -> {url, metadata, contents, audio, ...}.

2.
For each entry with an `url` value,
if the URL is GitHub, Zenodo, or Hugging Face, then
go to the relevant API and:
- get a date (all three), version (Zenodo), and license (all three)
- add those new datapoints into the `url` value.

3.
Overwrite the original file with this enrichment
(by default, it always _adds_ information).

This makes one syntactical change: `url` goes
from a plain string into a mapping: {value, date, license, source[, version]}
in a manner similar to what's already there for metadata.

See notes on individual functions for details including what the `date` means,
especially wrt GitHub where it is from the `pushed_at` endpoint (any branch).
This seems lke the simplest and cleanest solution for now,
but is debatable.

TODO
1. More APIs
2. Decide if individuals can manually enter this information
(maybe not for the APIs represented, to avoid the mixture).
3. Git action to run this every so often (every PR?)
4. Consider moving more URLs to supported APIs (where equivalent).
"""

import argparse
import re
import logging
import sys
import time

import requests
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

DEFAULT_FILEPATH = "./mir-datasets.yaml"
REQUEST_TIMEOUT = 10  # seconds
CHECKPOINT_EVERY = 20  # items
HEADERS = {"User-Agent": "apis-github-zenodo-script/1.0"}

ZENODO_URL_RE = re.compile(
    r"zenodo\.org/records?/(\d+)|doi\.org/10\.5281/zenodo\.(\d+)"
)

HF_RESERVED_SEGMENTS = {
    "tree", "blob", "resolve", "raw", "viewer",
    "discussions", "commits", "commit", "settings", "embed",
}

session = requests.Session()
session.headers.update(HEADERS)


class RateLimited(Exception):
    """Raised when GitHub tells us we're out of requests."""


def get_with_retries(url, retries=3, backoff=3, timeout=REQUEST_TIMEOUT):
    """
    `GET` with simple exponential backoff on
    timeouts, connection errors, 429s, and 5xxs.
    Raises `requests.RequestException` on final failure.
    """
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 429 or resp.status_code >= 500:
                raise requests.RequestException(
                    f"transient status {resp.status_code}"
                )
            return resp
        except requests.RequestException as exc:
            if attempt == retries:
                raise
            wait = backoff * attempt
            log.warning(
                "  ... request failed (%s), retrying in %ds (%d/%d)",
                exc, wait, attempt, retries,
            )
            time.sleep(wait)


def get_github_repo_info(repo_url):
    """
    Use GitHub API to get repo's last-pushed date and license, in one call.

    Returns
    (pushed_at, license_id) on success,
    (None, None) on failure.

    NB:
    This uses the repo endpoint's `pushed_at` field rather than the commits.
    Therefore date and license come from a single request
    Caveats wrt `pushed_at`:
      - updates on a push to *any* branch.
      - reflects push time, not commit time.
    For "when was this repo last updated", this is normally ok.
    For other use cases where exact default-branch commit timestamps matter,
    use the commits endpoint instead
    (which means a second API call).
    """
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        return None, None
    owner, repo = match.group(1), match.group(2)
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        resp = get_with_retries(api_url)
    except requests.RequestException as exc:
        log.warning("  ... GitHub request failed after retries: %s", exc)
        return None, None

    if resp.status_code == 403:
        if resp.headers.get("X-RateLimit-Remaining") == "0":
            reset = resp.headers.get("X-RateLimit-Reset")
            raise RateLimited(f"GitHub primary rate limit hit (resets at epoch {reset})")
        # Secondary/abuse rate limits don't carry X-RateLimit-Remaining, but
        # do carry a Retry-After header and/or a message body saying so.
        if resp.headers.get("Retry-After") or "secondary rate limit" in resp.text.lower():
            retry_after = resp.headers.get("Retry-After", "unspecified")
            raise RateLimited(
                f"GitHub secondary rate limit hit (retry after {retry_after}s)"
            )

    if resp.status_code != 200:
        log.warning("  ... GitHub API returned status %s", resp.status_code)
        return None, None

    try:
        repo_info = resp.json()
    except ValueError:
        log.warning("  ... GitHub returned non-JSON response")
        return None, None

    pushed_at = repo_info.get("pushed_at")
    license_info = repo_info.get("license") or {}
    license_id = license_info.get("spdx_id") or license_info.get("name")

    return pushed_at, license_id


def get_zenodo_published_info(zenodo_url):
    """
    Use Zenodo API to get publication date, version, and license.

    Returns
    (pub_date, version, license) on success,
    (None, None, None) on failure.

    Accepts URLs in the form of a
    1. direct URL: zenodo.org/records/<id>
    (optionally with a trailing `/versions/<n>`, which is ignored,
    and flexible wrt record/records as per `ZENODO_URL_RE` above)
    2. Zenodo DOI resolved via doi.org (`doi.org/10.5281/zenodo.<id>`)
    where 10.5281 is Zenodo's own DOI prefix.

    Either of the above forms yield the numeric record id.

    Uses whichever record ID appears in the URL (concept or specific version).
    A /versions/N URL (extension of the direct URL form) is resolved to that exact version.

    Handles both the
    - legacy `metadata.license.id` shape and the
    - newer `metadata.rights[].id`
    """
    match = ZENODO_URL_RE.search(zenodo_url)
    if not match:
        log.warning("  ... Zenodo format regex fail for %s", zenodo_url)
        return None, None, None
    record_id = match.group(1) or match.group(2)

    api_url = f"https://zenodo.org/api/records/{record_id}"
    try:
        resp = get_with_retries(api_url)
    except requests.RequestException as exc:
        log.warning("  ... Zenodo request failed after retries: %s", exc)
        return None, None, None

    if resp.status_code != 200:
        log.warning("  ... Zenodo API returned status %s", resp.status_code)
        return None, None, None

    try:
        meta = resp.json().get("metadata", {})
    except ValueError:
        log.warning("  ... Zenodo returned non-JSON response")
        return None, None, None

    pub_date = meta.get("publication_date", "")
    version = meta.get("version", "")

    # Legacy shape: metadata.license.id
    license_id = (meta.get("license") or {}).get("id")
    # Newer (InvenioRDM) shape: metadata.rights[0].id
    if not license_id:
        rights = meta.get("rights") or []
        if rights:
            license_id = rights[0].get("id") or rights[0].get("title", {}).get("en")

    return pub_date, version, license_id


def extract_hf_dataset_id(dataset_url):
    """
    Extract a Hugging Face dataset repo id from a URL of the form:
    - https://huggingface.co/datasets/<owner>/<name> (namespaced) or
    - https://huggingface.co/datasets/<name> (canonical, no namespace),

    Ignores
    - trailing path (/tree/main, /viewer, /blob/..., etc.)
    - query string.

    Returns
    the repo id (e.g. "owner/name" or "name"),
    or None if the URL doesn't match.
    """
    match = re.search(r"huggingface\.co/datasets/([^?#]+)", dataset_url)
    if not match:
        log.warning("  ... huggingface format regex fail for %s", dataset_url)
        return None

    segments = match.group(1).strip("/").split("/")
    repo_segments = []
    for seg in segments[:2]:
        if seg in HF_RESERVED_SEGMENTS:
            break
        repo_segments.append(seg)

    if not repo_segments:
        return None
    return "/".join(repo_segments)


def get_huggingface_dataset_info(dataset_url):
    """
    Use the Hugging Face Hub API to get a
    dataset's last-modified date and license, in one call.

    Returns
    (last_modified, license_id) on success,
    (None, None) on failure.

    `last_modified` is an ISO timestamp of the last change to
    the repo (any branch), analogous to GitHub's `pushed_at`.

    License is read from `cardData.license` when present (string or list),
    falling back to a `license:<id>` tag if not.
    """
    repo_id = extract_hf_dataset_id(dataset_url)
    if not repo_id:
        return None, None

    api_url = f"https://huggingface.co/api/datasets/{repo_id}"
    try:
        resp = get_with_retries(api_url)
    except requests.RequestException as exc:
        log.warning("  ... Hugging Face request failed after retries: %s", exc)
        return None, None

    if resp.status_code != 200:
        log.warning("  ... Hugging Face API returned status %s", resp.status_code)
        return None, None

    try:
        info = resp.json()
    except ValueError:
        log.warning("  ... Hugging Face returned non-JSON response")
        return None, None

    last_modified = info.get("lastModified")

    card_data = info.get("cardData") or {}
    license_val = card_data.get("license")
    if isinstance(license_val, list) and license_val:
        license_id = license_val[0]
    elif isinstance(license_val, str) and license_val:
        license_id = license_val
    else:
        license_id = None
        for tag in info.get("tags", []):
            if tag.startswith("license:"):
                license_id = tag.split(":", 1)[1]
                break

    return last_modified, license_id


def save(data, filepath):
    with open(filepath, "w") as f:
        yaml.safe_dump(
            # NB: this to reflect existing case-insensitive order...
            dict(sorted(data.items(), key=lambda kv: kv[0].lower())),
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )


def process_data(filepath: str = DEFAULT_FILEPATH, force: bool = False):
    """
    Load `filepath` (a mapping of dataset name -> record),
    enrich each record that has a `url`,
    and write the result back to the same file
    (with periodic checkpoint saves).

    The `url` value is upgraded from a plain string to a mapping:
    {value, date, license, source[, version]}.

    The `metadata`, `contents`, `audio`,
    and any other sibling keys on the record are left untouched
    (git diff should be clear and clean).

    Args:
        filepath: path to the YAML file to read and overwrite.
        force: if False, records whose `url` is already enriched with both
            `date` and `license` are skipped. If True, fetch and overwrite
            everything.
    """
    with open(filepath, "r") as f:
        data = yaml.safe_load(f) or {}

    total = len(data)
    processed_since_checkpoint = 0

    for i, (name, record) in enumerate(data.items(), 1):
        if not isinstance(record, dict):
            log.warning(
                "[%d/%d] %r is not a mapping (got %s), skipping",
                i, total, name, type(record).__name__,
            )
            continue

        url_field = record.get("url")
        if isinstance(url_field, dict):
            url = url_field.get("value", "")
            enriched = dict(url_field)
        else:
            url = url_field or ""
            enriched = {"value": url}

        if not url:
            continue

        if not force and enriched.get("date") and "license" in enriched:
            log.info("[%d/%d] %s (already processed, skipping)", i, total, name)
            continue

        log.info("[%d/%d] %s -> %s", i, total, name, url)
        matched_source = False

        try:
            if url.startswith("https://github.com/"):
                matched_source = True
                pushed_at, license_id = get_github_repo_info(url)
                if pushed_at:
                    enriched["date"] = pushed_at[:10]
                    enriched["source"] = "GitHub"
                    log.info("  ... pushed_at = %s", pushed_at)
                else:
                    log.warning("  ... could not retrieve pushed_at date")

                if license_id == "NOASSERTION":
                    # GH found a license file but couldn't map it to SPDX id.
                    # License is definitely not specified
                    # Record that explicitly as null rather than the
                    # GitHub-specific "NOASSERTION" string.
                    enriched["license"] = None
                    log.info("  ... license = null (GitHub: NOASSERTION)")
                elif license_id:
                    enriched["license"] = license_id
                    log.info("  ... license = %s", license_id)
                else:
                    log.warning("  ... could not retrieve license")

            elif "zenodo" in url:
                matched_source = True
                pub_date, version, license_id = get_zenodo_published_info(url)
                if pub_date:
                    enriched["date"] = pub_date
                    enriched["version"] = version
                    enriched["source"] = "Zenodo"
                    log.info("  ... %s | v%s", pub_date, version)
                else:
                    log.warning("  ... could not retrieve Zenodo info")
                if license_id:
                    enriched["license"] = license_id
                    log.info("  ... license = %s", license_id)
                else:
                    log.warning("  ... could not retrieve license")

            elif "huggingface.co/datasets/" in url:
                matched_source = True
                last_modified, license_id = get_huggingface_dataset_info(url)
                if last_modified:
                    enriched["date"] = last_modified[:10]
                    enriched["source"] = "HuggingFace"
                    log.info("  ... last_modified = %s", last_modified)
                else:
                    log.warning("  ... could not retrieve last_modified date")

                if license_id:
                    enriched["license"] = license_id
                    log.info("  ... license = %s", license_id)
                else:
                    log.warning("  ... could not retrieve license")

            if matched_source:
                record["url"] = enriched

        except RateLimited as exc:
            log.error("  ... %s", exc)
            log.error("Stopping early and saving progress so far.")
            save(data, filepath)
            log.info("Wrote partial progress to %s", filepath)
            sys.exit(1)

        except Exception:
            log.exception(
                "  ... unexpected error processing %s; skipping item and "
                "checkpointing progress",
                name,
            )
            save(data, filepath)
            processed_since_checkpoint = 0
            continue

        processed_since_checkpoint += 1
        if processed_since_checkpoint >= CHECKPOINT_EVERY:
            save(data, filepath)
            processed_since_checkpoint = 0
            log.info("  ... checkpoint saved")

    save(data, filepath)
    log.info("Wrote updated data back to %s", filepath)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch last-commit/publication dates, versions (Zenodo), "
        "and licenses for dataset URLs in a name-keyed YAML file, enriching "
        "each entry's `url` value in place."
    )
    parser.add_argument(
        "filepath",
        nargs="?",
        default=DEFAULT_FILEPATH,
        help=f"Path to the YAML file to process (default: {DEFAULT_FILEPATH})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch items even if dataset_url_date is already set",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    process_data(args.filepath, force=args.force)
