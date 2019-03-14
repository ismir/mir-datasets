import yaml
import urllib.request
import pytest


d = yaml.load(open("mir-datasets.yaml"))

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


def test_datasets(dataset):
    name = dataset[0]
    values = dataset[1]

    # check for spaces in beginning or end of name
    assert ' ' not in [name[0], name[-1]]

    # check if website is up
    code = urllib.request.urlopen(values['url'], timeout=5).getcode()
    assert code == 200

    # check if all required fields are there
    for field in required_fields:
        assert field in list(values.keys())
