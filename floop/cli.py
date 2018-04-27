import argparse

from sys import argv
from os.path import isfile
from .config import FloopConfig

_FLOOP_DEFAULT_CONFIGURATION_FILE = '~/.floop/config.json'
_FLOOP_DEFAULT_CONFIGURATION = {
    'device_target_directory' : '~/.floop/',
    'rsync_recursive' : True
}

class UnknownCommandException(Exception):
    pass

class FloopCLI(object):
    def __init__(self):
        self.devices, self.source_directory = FloopConfig().parse()
        parser = argparse.ArgumentParser(description='Floop CLI tool')
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(argv[1:2])
        if not hasattr(self, args.command):
            raise UnknownCommandException(args.command)
            exit(1)
        getattr(self, args.command)()

    def init(self):
        parser = argparse.ArgumentParser(
                description='Initialize communication between host and device(s)')
        print('Init...')
        if not isfile(_FLOOP_DEFAULT_CONFIGURATION_FILE):
            pass

    def push(self):
        parser = argparse.ArgumentParser(
                description='Push code from host to device(s)')
        print('push...')
        for device in self.devices:
            print(device.name)
            print(device.rsync(
                source_directory=self.source_directory,
                target_directory='~/.floop/',
                recursive=True
            ))
