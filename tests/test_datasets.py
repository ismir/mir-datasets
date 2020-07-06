import pytest

import urllib.request
from urllib.error import HTTPError
import warnings
import yaml


# open dataset file
with open('mir-datasets.yaml', 'rb') as hdl:
    d = yaml.load(hdl)

required_fields = [
    'url',
    'metadata',
    'contents',
    'audio'
]

def datasets():
    for name, values in d.items():
        yield name, values


@pytest.fixture(
    params=datasets(),
    ids=['%s' % k for k, l in datasets()]
)
def dataset(request):
    return request.param


def test_metadata(dataset):
    name = dataset[0]
    values = dataset[1]

    # check for spaces in beginning or end of name
    assert ' ' not in [name[0], name[-1]]

    # check if all required fields are there
    for field in required_fields:
        assert field in list(values.keys())


def test_url(dataset):
    values = dataset[1]

    parts = urllib.parse.urlparse(values['url'])
    assert parts.scheme.startswith('http')

