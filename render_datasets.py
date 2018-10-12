#!/usr/bin/env python
"""Render dataset list to a given format.

Example usage
-------------
$ ./render_datasets.py mir-datasets.yaml datasets.md
"""

import argparse
import os
import sys
import yaml

WORDPRESS_TEMPLATE = '''
dataset |  meta data |  contents |  with audio
--- | --- | --- | ---
'''

WORDPRESS_RECORD = ('<a title="{key}" href="{url}" target="_blank" rel="noopener">{title}</a> '
                    '| {metadata} | {contents} | {audio}')


def render_one(key, record):
    title = record.pop('title', key)

    metadata = record.pop('metadata', '')
    if isinstance(metadata, list):
        fields = []
        for item in metadata:
            if isinstance(item, dict):
                meta = list(item.keys())[0]
                item = '<a href="{}">{}</a>'.format(item[meta], meta)
            fields.append(item)
        metadata = ', '.join(fields)

    return WORDPRESS_RECORD.format(key=key, title=title, metadata=metadata, **record)


def render(records, format):

    records = sorted(records.items(), key=lambda x: x[0])

    lines = [render_one(key, record) for key, record in records]
    return WORDPRESS_TEMPLATE + '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)

    # Inputs
    parser.add_argument("dataset_file",
                        metavar="dataset_file", type=str,
                        help="Path to the dataset file.")
    parser.add_argument("output_file",
                        metavar="output_file", type=str,
                        help="Path to rendered output.")
    parser.add_argument("--format",
                        metavar="format", type=str, default='html',
                        help="Desired markdown format.")

    args = parser.parse_args()
    dataset = yaml.load(open(args.dataset_file))

    with open(args.output_file, 'w') as fp:
        fp.write(render(dataset, format=args.format))

    sys.exit(0 if os.path.exists(args.output_file) else 1)
