import pytest

import json

from os import remove
from os.path import abspath, dirname, isfile

from floop.config import FloopConfig, FloopConfigFileNotFound, CannotSetImmutableAttributeException, MalformedFloopConfigException, FloopSourceDirectoryDoesNotExist

_FLOOP_TEST_CONFIG_FILE = '{}/config.json'.format(dirname(
    abspath(__file__))
    )

_FLOOP_TEST_CONFIG = {
    'device_target_directory' : '/home/floop/.floop/',
    'docker_bin' : '/usr/local/bin/docker',
    'docker_compose_bin' : '/usr/local/bin/docker-compose',
    'docker_machine_bin' : '/usr/local/bin/docker-machine',
    'host_source_directory' : './',
    'devices' : [{
        'address' : '192.168.1.100',
        'name' : 'floop_test_0',
        'ssh_key' : '~/.ssh/id_rsa',
        'user' : 'floop'
        },]
}

@pytest.fixture(scope='function')
def fixture_valid_config_file(request):
    config_file = _FLOOP_TEST_CONFIG_FILE
    config = _FLOOP_TEST_CONFIG
    def cleanup():
        if isfile(config_file):
            remove(config_file)
    cleanup()
    with open(config_file, 'w') as cf:
        json.dump(config, cf)
    request.addfinalizer(cleanup)
    return config_file

def test_floop_config_init(fixture_valid_config_file):
    FloopConfig(fixture_valid_config_file)

def test_floop_config_validate(fixture_valid_config_file):
    FloopConfig(fixture_valid_config_file).validate()

def test_floop_config_nonexistent_file_does_not_validate():
    with pytest.raises(FloopConfigFileNotFound):
        FloopConfig('definitely/not/a/real/config').validate()

def test_floop_config_cannot_reset_config(fixture_valid_config_file):
    floop_config = FloopConfig(fixture_valid_config_file).validate()
    with pytest.raises(CannotSetImmutableAttributeException):
        floop_config.config = ''

def test_floop_config_not_all_config_keys_does_not_validate(fixture_valid_config_file):
    with open(fixture_valid_config_file) as cf:
        config = json.load(cf)
    del config[list(config.keys())[0]]
    floop_config = FloopConfig(fixture_valid_config_file)
    with pytest.raises(MalformedFloopConfigException):
        floop_config.config = config

def test_floop_config_not_all_device_keys_does_not_validate(fixture_valid_config_file):
    with open(fixture_valid_config_file) as cf:
        config = json.load(cf)
    del config['devices'][0][list(config['devices'][0].keys())[0]]
    floop_config = FloopConfig(fixture_valid_config_file)
    with pytest.raises(MalformedFloopConfigException):
        floop_config.config = config

def test_floop_config_parse(fixture_valid_config_file):
    FloopConfig(fixture_valid_config_file).validate().parse()

def test_floop_config_host_source_does_not_exist_does_not_parse(fixture_valid_config_file):
    with open(fixture_valid_config_file) as cf:
        config = json.load(cf)
    config['host_source_directory'] = './not/a/real/directory'
    floop_config = FloopConfig(fixture_valid_config_file)
    with pytest.raises(FloopSourceDirectoryDoesNotExist):
        floop_config.config = config
        floop_config.parse()

