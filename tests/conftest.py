import pytest

import os
import yaml


@pytest.fixture()
def root_dir():
    return os.path.join(os.path.dirname(__file__), os.path.pardir)


@pytest.fixture()
def mir_datasets_file(root_dir):
    return os.path.join(root_dir, 'mir-datasets.yaml')


@pytest.fixture()
def mir_datasets(mir_datasets_file):
    return yaml.load(open(mir_datasets_file))
