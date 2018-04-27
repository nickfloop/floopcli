import argparse
import json

from sys import argv
from os.path import isfile, dirname, expanduser
from os import makedirs, remove 
from util.termcolor import termcolor, cprint 
from .config import FloopConfig

_FLOOP_DEFAULT_CONFIGURATION_FILE = expanduser('~/.floop/config.json')
_FLOOP_DEFAULT_CONFIGURATION = {
    'device_target_directory' : '/home/floop/.floop/',
    'rsync_recursive' : True
}

class UnknownCommandException(Exception):
    pass

class FloopCLI(object):
    '''
    test
    '''
    def __init__(self):
        self.devices, self.source_directory = FloopConfig().parse()
        parser = argparse.ArgumentParser(description='Floop CLI tool')
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(argv[1:2])
        if not hasattr(self, args.command):
            raise UnknownCommandException(args.command)
            exit(1)
        getattr(self, args.command)()

    def __cprint(self, string, color=termcolor.DEFAULT):
        cprint(
            string=string,
            color=color,
            time=True,
            tag='floop')

    def configure(self):
        parser = argparse.ArgumentParser(
                description='Configure CLI settings for all projects')
        parser.add_argument('--overwrite',
                help='Overwrite configuration file with defaults',
                action='store_true')
        args = parser.parse_args(argv[2:])
        self.__cprint('Configure...')
        if not isfile(_FLOOP_DEFAULT_CONFIGURATION_FILE) or args.overwrite:
            makedirs(dirname(_FLOOP_DEFAULT_CONFIGURATION_FILE),
                    exist_ok=True)
            with open(_FLOOP_DEFAULT_CONFIGURATION_FILE, 'w') as c:
                json.dump(_FLOOP_DEFAULT_CONFIGURATION, c)
            self.__cprint('Wrote default configuration to file: {}'.format(
                _FLOOP_DEFAULT_CONFIGURATION_FILE
                )
            )
        else:
            self.__cprint('Configuration file already exists: {}'.format(
                _FLOOP_DEFAULT_CONFIGURATION_FILE
                )
            )

    def init(self):
        parser = argparse.ArgumentParser(
                description='Initialize single project communication between host and device(s)')
        print('Init...')

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
