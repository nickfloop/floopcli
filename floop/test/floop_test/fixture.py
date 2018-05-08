import pytest

import json

from os import remove
from os.path import abspath, dirname, isfile

from floop.config import _FLOOP_CONFIG_DEFAULT_CONFIGURATION

FLOOP_TEST_CONFIG_FILE = './floop.json' 

FLOOP_TEST_CONFIG = _FLOOP_CONFIG_DEFAULT_CONFIGURATION

@pytest.fixture(scope='function')
def fixture_valid_config_file(request):
    config_file = FLOOP_TEST_CONFIG_FILE
    config = FLOOP_TEST_CONFIG
    def cleanup():
        if isfile(config_file):
            remove(config_file)
    cleanup()
    with open(config_file, 'w') as cf:
        json.dump(config, cf)
    request.addfinalizer(cleanup)
    return config_file
