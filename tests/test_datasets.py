import yaml
import urllib.request
import pytest
from fake_useragent import UserAgent


# get fake user agent
ua = UserAgent()

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

    # check if website is up
    req = urllib.request.Request(values['url'], headers={'User-Agent' : ua.random}) 
    code = urllib.request.urlopen(req, timeout=5).getcode()

    assert (code == 200)
