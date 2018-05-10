import pytest

from os import remove
from os.path import abspath, dirname, isfile

from floop.config import Config, ConfigFileNotFound, CannotSetImmutableAttributeException, MalformedConfigException, SourceDirectoryDoesNotExist
from floop.test.floop_test.fixture import *

def test_floop_config_init(fixture_valid_config_file):
    Config(fixture_valid_config_file)

def test_floop_config_validate(fixture_valid_config_file):
    Config(fixture_valid_config_file).validate()

def test_floop_config_nonexistent_file_does_not_validate():
    with pytest.raises(ConfigFileNotFound):
        Config('definitely/not/a/real/config').validate()

def test_floop_config_cannot_reset_config(fixture_valid_config_file):
    floop_config = Config(fixture_valid_config_file).validate()
    with pytest.raises(CannotSetImmutableAttributeException):
        floop_config.config = ''

def test_floop_config_not_all_config_keys_does_not_validate(fixture_valid_config_file):
    with open(fixture_valid_config_file) as cf:
        config = json.load(cf)
    del config[list(config.keys())[0]]
    floop_config = Config(fixture_valid_config_file)
    with pytest.raises(MalformedConfigException):
        floop_config.config = config

def test_floop_config_not_all_device_keys_does_not_validate(fixture_valid_config_file):
    with open(fixture_valid_config_file) as cf:
        config = json.load(cf)
    del config['devices'][0][list(config['devices'][0].keys())[0]]
    floop_config = Config(fixture_valid_config_file)
    with pytest.raises(MalformedConfigException):
        floop_config.config = config

def test_floop_config_parse(fixture_valid_config_file):
    Config(fixture_valid_config_file).validate().parse()

def test_floop_config_host_source_does_not_exist_does_not_parse(fixture_valid_config_file):
    with open(fixture_valid_config_file) as cf:
        config = json.load(cf)
    config['host_source_directory'] = './not/a/real/directory'
    floop_config = Config(fixture_valid_config_file)
    with pytest.raises(SourceDirectoryDoesNotExist):
        floop_config.config = config
        floop_config.parse()

