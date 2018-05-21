import json
from time import time
from os import rename
from os.path import isdir, isfile
from shutil import which
from floop.iot.core import Core 

# default config to write when using floop config 
_FLOOP_CONFIG_DEFAULT_CONFIGURATION = {
    'groups' : {
        'default': { 
            'host_rsync_bin' : which('rsync'),
            'host_docker_machine_bin' : which('docker-machine'),
        },
        'group0' :{
            'cores' : {
                'default': {
                    'host_source' : './src/'
                },
                'core0' : {
                    'target_source' : '/home/floop/floop/',
                    'address' : '192.168.1.100', 
                    'user' : 'floop',             
                    'host_key' : '~/.ssh/id_rsa', 
                }
            }
        }
    },
}

def _flatten(config):
    flat_config = []
    try:
        default = config['groups']['default']
        for group, gval in config['groups'].items():
            if group != 'default':
                group_default = gval['cores']['default']
                for core, dval in gval['cores'].items():
                    if core != 'default':
                        core_config = default
                        for key, val in group_default.items():
                            core_config[key] = val
                        for key, val in dval.items():
                            core_config[key] = val
                        core_config['group'] = group
                        core_config['core'] = core
                        assert(core_config['address'])
                        flat_config.append(core_config)
        return flat_config
    # forces config to have default groups and cores
    except (TypeError, KeyError) as e:
        raise MalformedConfigException(str(e))

if __name__ == '__main__':
    print(_flatten(_FLOOP_CONFIG_DEFAULT_CONFIGURATION))

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

class MalformedCoreConfigException(Exception):
    '''
    At least one core in provided config did not have all expected keys
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

class RedundantCoreConfigException(Exception):
    '''
    At least one core in the config has a redundant name or address 
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
            dictionary of json file content
    '''
    with open(json_file) as j:
        return json.load(j)

class Config(object):
    def __init__(self, config_file):
        self.default_config = _FLOOP_CONFIG_DEFAULT_CONFIGURATION 
        self.config_file = config_file

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, value):
        if hasattr(self, 'config'):
            raise CannotSetImmutableAttributeException('config')
        self.__config = value

    def read(self):
        config_file = self.config_file
        if not isfile(config_file):
            raise ConfigFileDoesNotExist(config_file)
        raw_config = _read_json(config_file)
        # throws malformed errors
        config = _flatten(raw_config)
        addresses = []
        for core in config:
            if core['address'] in addresses:
                raise RedundantCoreConfigException(core['address'])
            addresses.append(core['address'])
        self.config = config
        return self

    def parse(self):
        # only handle dependency checking
        # let core handle host and target checking to prevent race
        for core in self.config:
            for key, val in core.items():
                if key.endswith('_bin'):
                    if not isfile(val):
                        err = 'Dependency {} not found at {}'.format(
                                key.replace('bin_'), val)
                        # TODO: test in an environment with unmet dependencies
                        raise UnmetHostDependencyException(err)
        cores = []
        for core in self.config:
            try:
                cores.append(Core(**core))
            except TypeError as e:
                missing_key = str(e).split(' ')[-1]
                err = '{} (core) has no {} (property)'.format(
                        core['core'], missing_key)
                raise MalformedConfigException(err)
        return cores
