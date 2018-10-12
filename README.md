# mir-datasets

This repository exists solely for tracking MIR datasets and their corresponding metadata
in a standardized, structured way. There are multiple consumers of this data:

* [audiocontentanalysis](http://audiocontentanalysis.org/data-sets/)
* [ISMIR datasets page](tbd)
* `<your instance here!>`

Importantly, [mir-datasets.yaml](https://github.com/ismir/mir-datasets/blob/master/mir-datasets.yaml) file is the **One Source of Truth** – all other formats and representations of this data (markdown, HTML, latex tables, what have you) should be derived from this master object. If there is some format for this table you would like to see, feel free to submit a [pull request](https://github.com/ismir/mir-datasets/pulls)!


## Schema

Each record in the [mir-datasets.yaml](https://github.com/ismir/mir-datasets/blob/master/mir-datasets.yaml) file adheres to one of the following formats:

```yaml
# Single metadata field
key1:
  url: http://path/to/website
  metadata: tempo
  contents: 123 songs
  audio: no

# Multiple metadata fields
key2:
  url: http://path/to/something.html
  metadata:
   - tempo
   - lyrics: http://my/lyrics/page
  contents: 10s snippets
  audio: yes
```

Note that multiple metadata fields additionally support providing URLs for each metadata field.


## Contributing

You are encouraged to add (or update) dataset listings in this file! When doing so, please try to
adhere to the following:

* **Preserve order in the list.** While this isn't technically necessary, it'll help others make sense of it.
* **Provide as much info as possible.**
* **Make sure that you've added valid YAML.** We ([will](https://github.com/ismir/mir-datasets/issues/1)) have tests, and they will (eventually) fail on Travis.


## Scripts

For now, the only output format supported is Markdown, which you can obtain via the following:

```bash
$ ./render_datasets.py mir-datasets.yaml datasets.md
```

Which will produce the output [data-sets.md](https://github.com/ismir/mir-datasets/blob/master/outputs/data-sets.md) file contained in this repository. Note that this output file **should not** be modified directly:

* If the information is incorrect, update the source YAML file
* If the formatting is wrong, please help fix the script (or [open an issue](https://github.com/ismir/mir-datasets/issues))
