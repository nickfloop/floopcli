import json
from os.path import isdir
from device.device import Device

_FLOOP_CONFIG_EXPECTED_KEYS = ['devices', 'source_directory']
_FLOOP_DEVICE_EXPECTED_KEYS = ['address', 'name']

class CannotSetImmutableAttributeException(Exception):
    pass

class MalformedFloopConfigException(Exception):
    pass

class MalformedFloopDeviceConfigException(Exception):
    pass

class FloopSourceDirectoryDoesNotExist(Exception):
    pass

def read_json(json_file):
    with open(json_file) as j:
        return json.load(j)

class FloopConfig(object):
    def __init__(self, config_file='example/test-config.json'):
        self.config = read_json(config_file)

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, value):
        if hasattr(self, 'config'):
            raise CannotSetImmutableAttributeException('config')
        config_keys = sorted(list(value.keys()))
        if config_keys != _FLOOP_CONFIG_EXPECTED_KEYS:
            raise MalformedFloopConfigException(config_keys) 
        self.__config = value

    def parse(self):
        if not isdir(self.config['source_directory']):
            raise FloopSourceDirectoryDoesNotExist(
                    self.config['source_directory'])
        source_directory = self.config['source_directory']
        devices = []
        for device in self.config['devices']:
            device_config = sorted(list(device.keys()))
            if device_config != _FLOOP_DEVICE_EXPECTED_KEYS:
                raise MalformedFloopDeviceConfigException(device_config)
            device = Device(address=device['address'], name=device['name']) 
            devices.append(device)
        return devices, source_directory
