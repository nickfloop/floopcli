import json
from time import time
from os import rename
from os.path import isdir, isfile
from pathlib import Path
from shutil import which
from floop.device.device import Device

_FLOOP_CONFIG_DEFAULT_CONFIGURATION = {
    'device_target_directory' : '/home/floop/floop/',
    'host_rsync_bin' : which('rsync'),
    'host_docker_bin' : which('docker'),
    # docker-compose binary should be compiled for ARM devices, so non-ARM
    # hosts need to exclude it from their path
    'host_docker_machine_bin' : which('docker-machine'),
    'host_source_directory' : './src/',
    'devices' : [{
        'address' : '192.168.1.122',
        'name' : 'floop0',
        'ssh_key' : '~/.ssh/id_rsa',
        'user' : 'floop'
        },]
}

class CannotSetImmutableAttributeException(Exception):
    pass

class MalformedConfigException(Exception):
    pass

class MalformedDeviceConfigException(Exception):
    pass

class SourceDirectoryDoesNotExist(Exception):
    pass

class ConfigFileNotFound(Exception):
    pass 

class TargetBuildFileDoesNotExist(Exception):
    pass 

class UnmetHostDependencyException(Exception):
    pass

def read_json(json_file):
    with open(json_file) as j:
        return json.load(j)

class Config(object):
    def __init__(self, config_file):
        self.default_config = _FLOOP_CONFIG_DEFAULT_CONFIGURATION 
        self.config_file = config_file
    
    def validate(self):
        config_file = self.config_file
        if not isfile(config_file):
            raise ConfigFileNotFound(config_file)
        self.config = read_json(config_file)
        for key, val in self.config.items():
            if key.endswith('_bin'):
                if val is None:
                    dependency_name = key.replace('_bin', '')
                    raise UnmetHostDependencyException(dependency_name)
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
            raise MalformedConfigException(config_keys) 
        for device in value['devices']:
            if len(set(device.keys()).intersection(
                _FLOOP_CONFIG_DEFAULT_CONFIGURATION['devices'][0].keys())) != \
                    len(_FLOOP_CONFIG_DEFAULT_CONFIGURATION['devices'][0].keys()):
                raise MalformedConfigException(config_keys) 
        self.__config = value

    def parse(self):
        if not isdir(self.config['host_source_directory']):
            raise SourceDirectoryDoesNotExist(
                    self.config['host_source_directory']
                  )
        source_directory = self.config['host_source_directory']
        target_directory = self.config['device_target_directory']
        docker_machine_bin = self.config['host_docker_machine_bin']
        devices = []
        for device in self.config['devices']:
            devices.append(
                Device(
                    docker_machine_bin=docker_machine_bin,
                    **device))
        return devices, source_directory, target_directory
