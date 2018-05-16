import json
from time import time
from os import rename
from os.path import isdir, isfile
from pathlib import Path
from shutil import which
from floop.device.device import Device

# default config to write when using floop config 
_FLOOP_CONFIG_DEFAULT_CONFIGURATION = {
    'device_target_directory' : '/home/floop/floop/',
    'host_source_directory' : './src/',
    'host_rsync_bin' : which('rsync'),
    'host_docker_machine_bin' : which('docker-machine'),
    'devices' : [{
        'address' : '192.168.1.100', # e.g. 192.168.1.100
        'name' : 'floop0',           # e.g. floop0
        'ssh_key' : '~/.ssh/id_rsa', # e.g. ~/.ssh/id_rsa
        'user' : 'floop'             # e.g. floop
        },]
}

class CannotSetImmutableAttributeException(Exception):
    '''
    Tried to set immutable attribute after initialization
    '''
    pass

class MalformedConfigException(Exception):
    '''
    Provided config did not have all expected keys
    '''
    pass

class MalformedDeviceConfigException(Exception):
    '''
    At least one device in provided config did not have all expected keys
    '''
    pass

class SourceDirectoryDoesNotExist(Exception):
    '''
    Provided config "host_source_directory" does not exist
    '''
    pass

class ConfigFileDoesNotExist(Exception):
    '''
    Provided configuration file does not exist
    '''
    pass 

class TargetBuildFileDoesNotExist(Exception):
    '''
    Provided "host_source_directory" in config has no Dockerfile
    '''
    pass 

class UnmetHostDependencyException(Exception):
    '''
    Provided dependency binary path does not exist
    '''
    pass

class RedundantDeviceConfigException(Exception):
    '''
    At least one device in the config has a redundant name or address 
    '''
    pass

def _read_json(json_file):
    '''
    Convenient wrapper for reading .json file into dict

    Args:
        json_file (str):
            Path to json file
    Returns:
        dict:
            dictionary of .json file content
    '''
    with open(json_file) as j:
        return json.load(j)

class Config(object):
    def __init__(self, config_file):
        self.default_config = _FLOOP_CONFIG_DEFAULT_CONFIGURATION 
        self.config_file = config_file
    
    def validate(self):
        config_file = self.config_file
        if not isfile(config_file):
            raise ConfigFileDoesNotExist(config_file)
        self.config = _read_json(config_file)
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
        addresses = []
        names = []
        for device in value['devices']:
            if len(set(device.keys()).intersection(
                _FLOOP_CONFIG_DEFAULT_CONFIGURATION['devices'][0].keys())) != \
                    len(_FLOOP_CONFIG_DEFAULT_CONFIGURATION['devices'][0].keys()):
                raise MalformedConfigException(config_keys) 
            if device['address'] in addresses or device['name'] in names:
                raise RedundantDeviceConfigException(device['name'])
            addresses.append(device['address'])
            names.append(device['name'])
        self.__config = value

    def parse(self):
        # TODO: check that device names are unique
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
