import pytest

import os


@pytest.fixture()
def root_dir():
    return os.path.join(os.path.dirname(__file__), os.path.pardir)


@pytest.fixture()
def mir_datasets_file(root_dir):
    return os.path.join(root_dir, 'mir-datasets.yaml')
