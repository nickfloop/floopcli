import argparse
import json
import logging

from sys import argv, exit, modules
from shutil import copyfile
from functools import partial
from os.path import isfile, dirname, expanduser, abspath
from os import makedirs, remove 
from multiprocessing import Pool
from platform import system
from time import time
from floop.util.termcolor import termcolor, cprint 
from floop.device.device import build, create, destroy, logs, ps, push, run, test, DeviceSourceDirectoryDoesNotExist
from .config import Config, ConfigFileNotFound, SourceDirectoryDoesNotExist, MalformedConfigException, UnmetHostDependencyException

_FLOOP_CONFIG_DEFAULT_FILE = './floop.json'

_FLOOP_USAGE_STRING = '''
floop [-c custom-config.json] <command> [<args>]

Supported commands:
    config      Generate a default configuration file: {}
    create      Ini
    ls
    logs
    push
    build
    run
    clean
'''

class IncompatibleCommandLineOptions(Exception):
    pass

class FloopCLI(object):
    #TODO: make all calls parallel and async
    '''
    CLI entry point, handles all CLI calls

    Parses all CLI commands then calls the appropriate
    class method matching the CLI commands

    attributes:
        config (floop.config.Config):  
            configuration used during CLI call
        source_directory (str):
            filepath of source code directory on host
        target_directory (str):
            filepath of source code directory on target (must be fullpath)
        devices ([:py:class:`floop.device.device.Device`]):
            list of devices defined in configuration file 
    '''
    def __init__(self):
        parser = argparse.ArgumentParser(description='Floop CLI tool',
                usage=_FLOOP_USAGE_STRING)
        parser.add_argument('-c', '--config-file', 
                help='Specify a non-default configuration file')
        parser.add_argument('command', help='Subcommand to run')
        # index of the command to be parsed below
        config_file = _FLOOP_CONFIG_DEFAULT_FILE
        try:
            self.command_index = 2
            if len(argv) > 3:
                if argv[1] not in ['-c', '-config-file']:
                    args = parser.parse_args(argv[1:2])
                else:
                    args = parser.parse_args(argv[1:4])
                if 'config' in argv and args.config_file:
                    raise IncompatibleCommandLineOptions('-c and config')
                if args.config_file:
                    config_file = args.config_file
                    self.command_index = 4 
            elif len(argv) > 1:
                if argv[1] in ['-c', '-config-file']:
                    args = parser.parse_args(argv[1:3])
                else:
                    args = parser.parse_args(argv[1:2])
            else:
                parser.print_help()
                exit(1)
            if not hasattr(self, args.command):
                exit('Unknown floop command: {}'.format(args.command))
            if args.command != 'config':
                floop_config = Config(
                        config_file=config_file).validate()
                self.config = floop_config.config
                self.devices, self.source_directory, self.target_directory = floop_config.parse()
            # this runs the method matching the CLI argument
            getattr(self, args.command)()
        # all CLI stdout/stderr output should come from here
        except IncompatibleCommandLineOptions:
            exit('''Error| Incompatible commands and flags: -c and config\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tUse the -c flag to point to a non-default config file: floop -c your-config-file.json'\n\
\tGenerate a default config file by running: floop config\n\
\tCopy an existing floop config file to the default path: {}\n\
\tOnly use one of the following: -c or config\n\
'''.format(_FLOOP_CONFIG_DEFAULT_FILE))
        except ConfigFileNotFound:
            exit('Error| floop config file not found: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCopy an existing floop config file to the default path: {}\n\
\tGenerate a default config file by running: floop config\n\
\tUse the -c flag to point to a non-default config file: floop -c your-config-file.json'.format(
    config_file, _FLOOP_CONFIG_DEFAULT_FILE))
        except (SourceDirectoryDoesNotExist, DeviceSourceDirectoryDoesNotExist):
            exit('''Error| Cannot find host_source_directory in config file: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tMake a new host_source_directory and define it in config file\n\
\tChange host_source_directory in config file to a valid filepath\n\
\tMake sure you have permission to access the files in host_source_directory'''.format(config_file))
        except MalformedConfigException:
            exit('''Error| Config file is malformed: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCopy an existing valid floop config file to the default path: {}\n\
\tGenerate a default config file by running: floop config\n\
\tUse the -c flag to point to a non-default config file: floop -c your-config-file.json'\n\
'''.format(config_file, _FLOOP_CONFIG_DEFAULT_FILE))
        except UnmetHostDependencyException as e:
            exit('''Error| Unmet dependency on host: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tInstall dependency for your operating system\n\
'''.format(str(e)))
        
    def __cprint(self, string, color=termcolor.DEFAULT):
        '''
        Wrapper for internal color print

        args:
            string: 
                string to print
            color:
                terminal color name
        '''
        cprint(
            string=string,
            color=color,
            time=True,
            tag='floop')

    def config(self):
        '''
        Generate default configuration file
        '''
        parser = argparse.ArgumentParser(
                description='Configure CLI settings for all projects')
        parser.add_argument('-o', '--overwrite',
                help='Overwrite configuration file with defaults',
                action='store_true')
        args = parser.parse_args(argv[2:])
        self.__cprint('Configure...')
        if isfile(_FLOOP_CONFIG_DEFAULT_FILE):
            self.__cprint('Configuration file already exists: {}'.format(
                _FLOOP_CONFIG_DEFAULT_FILE
                )
            )
            # if the file exists and will not be overwritten, just move on
            if not args.overwrite:
                return
            backup_file = '{}.backup-{}'.format(_FLOOP_CONFIG_DEFAULT_FILE, time())
            copyfile(_FLOOP_CONFIG_DEFAULT_FILE, backup_file)
            self.__cprint('Copied existing config file {} to backup file: {}'.format(
                _FLOOP_CONFIG_DEFAULT_FILE, backup_file))
        makedirs(dirname(_FLOOP_CONFIG_DEFAULT_FILE),
                exist_ok=True)
        with open(_FLOOP_CONFIG_DEFAULT_FILE, 'w') as c:
            json.dump(Config(_FLOOP_CONFIG_DEFAULT_FILE).default_config, c)
        self.__cprint('Wrote default configuration to file: {}'.format(
            _FLOOP_CONFIG_DEFAULT_FILE
            )
        )

    def create(self):
        # TODO: add --check flag to check ssh communication with a collection of enumerated commands
        parser = argparse.ArgumentParser(
                description='Initialize single project communication between host and device(s)')
        with Pool() as pool:
            pool.map(create, self.devices)

    def ps(self):
        # TODO: add metrics command to get resource usage info AND process info
        parser = argparse.ArgumentParser(
                description='List all initiated device(s)')
        print('ps...')
        with Pool() as pool:
            pool.map(ps, self.devices)
     
    def logs(self):
        # TODO: add -f option (bonus if it's pipe-able)
        parser = argparse.ArgumentParser(
                description='Logs from initialized device(s)')
        print('logs...')
        with Pool() as pool:
            pool.map(logs, self.devices)

    def push(self):
        # TODO: add .floopignore ?
        parser = argparse.ArgumentParser(
                description='Push code from host to device(s)')
        print('push...')
        with Pool() as pool:
            pool.map(
                    partial(push,
                        source_directory=self.source_directory,
                        target_directory=self.target_directory),
                    self.devices)

    def build(self):
        # TODO: add -v command to tee build outputs to logs AND local stdout
        parser = argparse.ArgumentParser(
                description='Build code on device(s)')
        print('build...')
        #self.push()
        with Pool() as pool:
            pool.map(
                    partial(build,
                        source_directory=self.source_directory,
                        target_directory=self.target_directory),
                    self.devices)

    def run(self):
        # TODO: add -v command to tee build outputs to logs AND local stdout
        parser = argparse.ArgumentParser(
                description='Run code on device(s)')
        print('run...')
        with Pool()as pool:
            pool.map(
                    partial(run,
                        source_directory=self.source_directory,
                        target_directory=self.target_directory),
                    self.devices)
                
    def test(self):
        # TODO: check that test YAML exists
        parser = argparse.ArgumentParser(
                description='Test code on device(s)')
        print('test...')
        test_command = 'docker build'
        with Pool()as pool:
            pool.map(
                    partial(test,
                        source_directory=self.source_directory,
                        target_directory=self.target_directory),
                    self.devices)

    def destroy(self):
        parser = argparse.ArgumentParser(
                description='Destroy project, code, and environment on device(s) but not host')
        print('clean...')
        with Pool() as pool:
            pool.map(destroy, self.devices)
