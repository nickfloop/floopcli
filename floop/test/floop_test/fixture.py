import pytest

import json

from os import remove
from os.path import abspath, dirname, isfile

FLOOP_TEST_CONFIG_FILE = './floop.json' 
#'{}/floop.json'.format(dirname(
#    abspath(__file__))
#    )

FLOOP_TEST_CONFIG = {
    'device_target_directory' : '/home/floop/floop/',
    'docker_bin' : '/usr/local/bin/docker',
    'docker_compose_bin' : '/usr/local/bin/docker-compose',
    'docker_machine_bin' : '/usr/local/bin/docker-machine',
    'host_source_directory' : './example/src/',
    'devices' : [{
        'address' : '192.168.1.122',
        'name' : 'op0',
        'ssh_key' : '~/.ssh/id_rsa',
        'user' : 'floop'
        },]
}

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
