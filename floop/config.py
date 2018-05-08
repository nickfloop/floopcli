import json
from time import time
from os import rename
from os.path import isdir, isfile
from shutil import which
from floop.device.device import Device

# TODO: use which or equivalent to populate automatically, fall back to defaults
_FLOOP_CONFIG_DEFAULT_CONFIGURATION = {
    'device_target_directory' : '/home/floop/floop/',
    'rsync_bin' : which('rsync') or '/usr/bin/rsync',
    'docker_bin' : which('docker') or '/usr/bin/docker',
    'docker_compose_bin' : which('docker-compose') or '/usr/local/bin/docker-compose',
    'docker_machine_bin' : which('docker-machine') or '/usr/local/bin/docker-machine',
    'host_source_directory' : './src/',
    'devices' : [{
        'address' : '192.168.1.100',
        'name' : 'floop0',
        'ssh_key' : '~/.ssh/id_rsa',
        'user' : 'floop'
        },]
}

class CannotSetImmutableAttributeException(Exception):
    pass

class MalformedFloopConfigException(Exception):
    pass

class MalformedFloopDeviceConfigException(Exception):
    pass

class FloopSourceDirectoryDoesNotExist(Exception):
    pass

class FloopConfigFileNotFound(Exception):
    pass 

def read_json(json_file):
    with open(json_file) as j:
        return json.load(j)

class FloopConfig(object):
    def __init__(self, config_file):
        self.default_config = _FLOOP_CONFIG_DEFAULT_CONFIGURATION 
        self.config_file = config_file
    
    def validate(self):
        config_file = self.config_file
        if not isfile(config_file):
            raise FloopConfigFileNotFound(config_file)
        self.config = read_json(config_file)
        return self

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, value):
        if hasattr(self, 'config'):
            raise CannotSetImmutableAttributeException('config')
        config_keys = sorted(list(value.keys()))
        # extra keys will be ignored
        if len(set(config_keys).intersection(_FLOOP_CONFIG_DEFAULT_CONFIGURATION.keys())) != \
                len(_FLOOP_CONFIG_DEFAULT_CONFIGURATION.keys()):
            raise MalformedFloopConfigException(config_keys) 
        for device in value['devices']:
            if len(set(device.keys()).intersection(
                _FLOOP_CONFIG_DEFAULT_CONFIGURATION['devices'][0].keys())) != \
                    len(_FLOOP_CONFIG_DEFAULT_CONFIGURATION['devices'][0].keys()):
                raise MalformedFloopConfigException(config_keys) 
        self.__config = value

    def parse(self):
        if not isdir(self.config['host_source_directory']):
            raise FloopSourceDirectoryDoesNotExist(
                    self.config['host_source_directory']
                  )
        source_directory = self.config['host_source_directory']
        docker_machine_bin = self.config['docker_machine_bin']
        devices = []
        for device in self.config['devices']:
            devices.append(
                Device(
                    docker_machine_bin=docker_machine_bin,
                    **device))
        return devices, source_directory
