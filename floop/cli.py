import argparse
import json

from sys import argv, exit
from os.path import isfile, dirname, expanduser
from os import makedirs, remove 
from platform import system
from floop.util.termcolor import termcolor, cprint 
from .config import FloopConfig, FloopConfigFileNotFound, FloopSourceDirectoryDoesNotExist

_FLOOP_CONFIG_DEFAULT_FILE = './floop.json'

_FLOOP_USAGE_STRING = '''
floop [-c custom-config.json] <command> [<args>]

Supported commands:
    config
    init
    ls
    logs
    push
    build
    run
    clean
'''

class FloopCLI(object):
    '''
    test
    '''
    def __init__(self):
        operating_system = system()
        if operating_system != 'Linux':
            exit('Unsupported operating system: {}'.format(operating_system))
        parser = argparse.ArgumentParser(description='Floop CLI tool',
                usage=_FLOOP_USAGE_STRING)
        parser.add_argument('-c', '--config-file', 
                help='Specify a non-default configuration file')
        parser.add_argument('command', help='Subcommand to run')
        command_index = 1 
        config_file = _FLOOP_CONFIG_DEFAULT_FILE
        try:
            if len(argv) > 3:
                args = parser.parse_args(argv[1:])
                if argv[-1] == 'config' and args.config_file:
                    exit('err')
            if len(argv) > 2:
                if argv[1] != 'config':
                    args = parser.parse_args(argv[1:])
                    if args.config_file:
                        command_index = 3 
                        config_file = args.config_file
                        self.devices, self.source_directory = FloopConfig(
                                config_file=config_file).validate().parse()
            elif len(argv) > 1:
                args = parser.parse_args(argv[1:])
                if not args.command == 'config':
                    self.devices, self.source_directory = FloopConfig(
                            config_file=config_file).validate().parse()
        except FloopConfigFileNotFound:
            exit('Error| floop config file not found: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCopy an existing floop config file to the default path: {}\n\
\tGenerate a default config file by running: floop config\n\
\tUse the -c flag to point to a non-default config file: floop -c your-config-file.json'.format(
    config_file, _FLOOP_CONFIG_DEFAULT_FILE))
        except FloopSourceDirectoryDoesNotExist:
            exit('Error| Cannot find host_source_directory in config file: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tMake a new host_source_directory and define it in config file\n\
\tChange host_source_directory in config file to a valid filepath\n\
\tMake sure you have permission to access the files in host_source_directory'.format(config_file))
        self.config_file = config_file
        args = parser.parse_args(argv[command_index:command_index+1])
        if not hasattr(self, args.command):
            exit('Unknown floop command: {}'.format(args.command))
        # this runs the method matching the CLI argument
        getattr(self, args.command)()

    def __cprint(self, string, color=termcolor.DEFAULT):
        cprint(
            string=string,
            color=color,
            time=True,
            tag='floop')

    def config(self):
        # TODO: back up old config file
        parser = argparse.ArgumentParser(
                description='Configure CLI settings for all projects')
        parser.add_argument('-o', '--overwrite',
                help='Overwrite configuration file with defaults',
                action='store_true')
        args = parser.parse_args(argv[2:])
        self.__cprint('Configure...')
        if not isfile(_FLOOP_CONFIG_DEFAULT_FILE) or args.overwrite:
            makedirs(dirname(_FLOOP_CONFIG_DEFAULT_FILE),
                    exist_ok=True)
            with open(_FLOOP_CONFIG_DEFAULT_FILE, 'w') as c:
                json.dump(FloopConfig(_FLOOP_CONFIG_DEFAULT_FILE).default_config, c)
            self.__cprint('Wrote default configuration to file: {}'.format(
                _FLOOP_CONFIG_DEFAULT_FILE
                )
            )
        else:
            self.__cprint('Configuration file already exists: {}'.format(
                _FLOOP_CONFIG_DEFAULT_FILE
                )
            )

    def init(self):
        # TODO: install docker
        # TODO: install docker-machine
        # TODO: download docker-compose binary
        # TODO: add --check flag to check ssh communication with a collection of enumerated commands
        parser = argparse.ArgumentParser(
                description='Initialize single project communication between host and device(s)')
        print('Init...')
        if len(self.devices) < 1:
            exit('No devices defined in configuration file: {}'.format(
                self.config_file))
        for device in self.devices:
            device.create()

    def ls(self):
        # TODO: add metrics command to get resource usage info AND process info
        parser = argparse.ArgumentParser(
                description='List all initiated device(s)')
        print('ls...')
        ls_command = 'docker ps'
        for device in self.devices:
            device.run_ssh_command(ls_command)
     
    def logs(self):
        # TODO: add -f option (bonus if it's pipe-able)
        parser = argparse.ArgumentParser(
                description='Logs from initialized device(s)')
        print('logs...')
        logs_command = 'docker-compose logs'
        for device in self.devices:
            device.run_ssh_command(logs_command)

    def push(self):
        # TODO: add .floopignore ?
        parser = argparse.ArgumentParser(
                description='Push code from host to device(s)')
        print('push...')
        for device in self.devices:
            print(device.name)
            print(device.rsync(
                source_directory=self.source_directory,
                target_directory='/.floop/',
                recursive=True
            ))

    def build(self):
        # TODO: add -v command to tee build outputs to logs AND local stdout
        parser = argparse.ArgumentParser(
                description='Build code on device(s)')
        print('build...')
        build_command = 'docker-compose build'
        for device in self.devices:
            device.run_ssh_command(build_command)

    def run(self):
        # TODO: add -v command to tee build outputs to logs AND local stdout
        parser = argparse.ArgumentParser(
                description='Run code on device(s)')
        print('run...')
        run_command = 'docker-compose up -d'
        for device in self.devices:
            device.run_ssh_command(run_command)

    def test(self):
        # TODO: check that test YAML exists
        parser = argparse.ArgumentParser(
                description='Test code on device(s)')
        print('test...')
        test_command = 'docker-compose -f {}/docker-compose.yml.test up -d'
        for device in self.devices:
            device.run_ssh_command(test_command)

    def clean(self):
        parser = argparse.ArgumentParser(
                description='Clean project, code, and environment from device(s) but not host')
        print('clean...')
        for device in self.devices:
            device.clean()
