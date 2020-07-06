#!/usr/bin/env python
"""Render dataset list to a given format.

Example usage
-------------
$ ./render_datasets.py mir-datasets.yaml datasets.md
$ ./render_datasets.py mir-datasets.yaml datasets.js
"""

import argparse
import markdown
import joblib
import json
import os
import requests
import sys
import yaml


MARKDOWN_TEMPLATE = '''
status| dataset |  metadata |  contents |  with audio
--- | --- | --- | --- | ---
'''

MARKDOWN_RECORD = ('{status} | '
                   '<a title="{key}" href="{url}" target="_blank" rel="noopener">{title}</a> '
                   '| {metadata} | {contents} | {audio}')

HEALTH = {
    0: '&#x2705;',
    1: '&#x2620;'
}


def get_url_status(url):
    try:
        response = requests.get(url, timeout=3)
        status_code = response.status_code
    except requests.exceptions.ConnectionError as derp:
        status_code = 666
    return HEALTH[status_code >= 400]


def render_one(key, record):
    title = record.pop('title', key)

    status = get_url_status(record['url'])
    metadata = record.pop('metadata', '')
    if isinstance(metadata, list):
        fields = []
        for item in metadata:
            if isinstance(item, dict):
                meta = list(item.keys())[0]
                item = '[{}]({})'.format(meta, item[meta])
            fields.append(item)
        metadata = ', '.join(fields)

    return MARKDOWN_RECORD.format(key=key, title=title, metadata=metadata, 
                                  status=status, **record)


def render(records, output_format, n_jobs=-1, verbose=0):
    '''Render a number of records to the given output format.

    Parameters
    ----------
    records : dict
        Dataset records

    output_format : str
        One of ['md', 'js']

    Returns
    -------
    data : str
        String data to write to file.
    '''
    records = sorted(records.items(), key=lambda x: x[0].lower())
    
    # Fan out
    pool = joblib.Parallel(n_jobs=n_jobs, verbose=verbose)
    dfx = joblib.delayed(render_one)
    lines = pool(dfx(key, record) for key, record in records)

    md = MARKDOWN_TEMPLATE + '\n'.join(lines)

    if output_format == 'js':
        html = markdown.markdown(md, extensions=['extra', 'smarty'], output_format='html5')
        output = "document.write({})".format(json.dumps(html.replace('\n', '')))
    elif output_format == 'md':
        output = md
    else:
        raise ValueError("unsupported output format: {}".format(output_format))

    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)

    # Inputs
    parser.add_argument("dataset_file",
                        metavar="dataset_file", type=str,
                        help="Path to the dataset file.")
    parser.add_argument("output_file",
                        metavar="output_file", type=str,
                        help="Path to rendered output.")
    parser.add_argument("--n_jobs",
                        metavar="n_jobs", type=int, default=1,
                        help="Number of CPUs to use for parallelization (-1 for all).")
    parser.add_argument("--verbose",
                        metavar="verbose", type=int, default=0,
                        help="Verbosity level, 0 for nothing, >1 for something.")

    args = parser.parse_args()
    dataset = yaml.load(open(args.dataset_file), Loader=yaml.FullLoader)

    output_format = os.path.splitext(args.output_file)[-1].strip('.')
    with open(args.output_file, 'w') as fp:
        fp.write(render(dataset, output_format, 
                        n_jobs=args.n_jobs, verbose=args.verbose))

    sys.exit(0 if os.path.exists(args.output_file) else 1)
