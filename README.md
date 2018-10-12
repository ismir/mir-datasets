# mir-datasets

This repository exists solely for tracking MIR datasets and their corresponding metadata
in a standardized, structured way. There are multiple consumers of this data:

* [audiocontentanalysis](http://audiocontentanalysis.org/data-sets/)
* [ISMIR datasets page](tbd)
* `<your instance here!>`


## Schema

Each record in the [mir-datasets.yaml]() file adheres to one of the following formats:

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

