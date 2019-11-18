# mir-datasets

[![Build Status](https://travis-ci.com/ismir/mir-datasets.svg?branch=master)](https://travis-ci.com/ismir/mir-datasets)

This repository exists solely for tracking MIR datasets and their corresponding metadata
in a standardized, structured way. There are multiple consumers of this data:

* [audiocontentanalysis](http://audiocontentanalysis.org/data-sets/)
* [ISMIR datasets page](http://www.ismir.net/resources/datasets/)
* `<your instance here!>`

Importantly, [mir-datasets.yaml](https://github.com/ismir/mir-datasets/blob/master/mir-datasets.yaml) file is the **One Source of Truth** – all other formats and representations of this data (markdown, HTML, latex tables, what have you) should be derived from this master object. If there is some format for this table you would like to see, feel free to submit a [pull request](https://github.com/ismir/mir-datasets/pulls)!


## Acknowledgement

This effort extends years of effort by [Alexander Lerch](https://github.com/alexanderlerch) to maintain a rolling list of MIR datasets on his [website](http://audiocontentanalysis.org/data-sets/). Many thanks and high fives for the diligent work and foresight to recognize the value this collection has to the ISMIR community and beyond!


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

You can render the output as either Markdown or Javascript by specifying the correct output format, via the following:

```bash
$ ./render_datasets.py mir-datasets.yaml outputs/mir-datasets.js
```

Which will produce the output [data-sets.md](https://github.com/ismir/mir-datasets/blob/master/outputs/mir-datasets.js) file contained in this repository. Note that this output file **should not** be modified directly:

* If the information is incorrect, update the source YAML file
* If the formatting is wrong, please help fix the script (or [open an issue](https://github.com/ismir/mir-datasets/issues))


## Testing

You can verify that the JS table is produced correctly by running a local HTTP server from the repository root, which points to `index.html`. 

```bash
python -m http.server
```

Note that the table will inherit the CSS of the page that renders it. 


## ISMIR-Home

This repository serves the datasets information on the ISMIR website. We have made a conscious choice to make this work with static web technologies. While this makes serving easier, it requires that the ISMIR website consume this table as a JS source. This repository achieves this through the following:

* maintain a markdown table here
* when updated, render it as JS 
* commit to the repository (manually)
* serve as an asset via github pages

There is opportunity to automate this via e.g. Travis-CI, but the velocity on this repository hasn't been high enough to warrant it yet.
