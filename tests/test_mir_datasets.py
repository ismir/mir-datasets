import pytest

import yaml


def test_load_yaml(mir_datasets_file):
    dataset = yaml.load(open(mir_datasets_file))
    assert len(dataset) > 100


@pytest.fixture()
def mir_datasets(mir_datasets_file):
    return yaml.load(open(mir_datasets_file))


def validate_entries(obj):
    assert str(obj['url']).startswith('http')
    assert len(str(obj['audio'])) > 0
    assert len(str(obj['contents'])) > 0
    meta = obj.get('metadata', [])
    if isinstance(meta, str):
        assert len(meta) > 0
    elif isinstance(meta, list):
        for item in meta:
            if isinstance(item, str):
                assert len(item) > 0
            elif isinstance(item, dict):
                assert len(item) == 1
                assert str(list(item.values())[0]).startswith('http')
            else:
                raise ValueError('malformed metadata item: {}'.format(item))
    else:
        raise ValueError("'metadata' is neither a string nor list: {}".format(meta))


def test_entries(mir_datasets):
    for key, entry in mir_datasets.items():
        validate_entries(entry)
