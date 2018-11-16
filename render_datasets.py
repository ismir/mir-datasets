#!/usr/bin/env python
"""Render dataset list to a given format.

Example usage
-------------
$ ./render_datasets.py mir-datasets.yaml datasets.md
$ ./render_datasets.py mir-datasets.yaml datasets.js
"""

import argparse
import markdown
import json
import os
import sys
import yaml

MARKDOWN_TEMPLATE = '''
dataset |  meta data |  contents |  with audio
--- | --- | --- | ---
'''

MARKDOWN_RECORD = ('<a title="{key}" href="{url}" target="_blank" rel="noopener">{title}</a> '
                   '| {metadata} | {contents} | {audio}')


def render_one(key, record):
    title = record.pop('title', key)

    metadata = record.pop('metadata', '')
    if isinstance(metadata, list):
        fields = []
        for item in metadata:
            if isinstance(item, dict):
                meta = list(item.keys())[0]
                item = '[{}]({})'.format(meta, item[meta])
            fields.append(item)
        metadata = ', '.join(fields)

    return MARKDOWN_RECORD.format(key=key, title=title, metadata=metadata, **record)


def render(records, output_format):
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
    lines = [render_one(key, record) for key, record in records]
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

    args = parser.parse_args()
    dataset = yaml.load(open(args.dataset_file))

    output_format = os.path.splitext(args.output_file)[-1].strip('.')
    with open(args.output_file, 'w') as fp:
        fp.write(render(dataset, format=output_format))

    sys.exit(0 if os.path.exists(args.output_file) else 1)
