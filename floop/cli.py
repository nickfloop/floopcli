import argparse
import json
import logging

from pkg_resources import require, DistributionNotFound
from sys import argv, exit, modules
from shutil import copyfile
from functools import partial
from os.path import isfile, dirname, expanduser, abspath
from os import makedirs, remove 
from multiprocessing import Pool
from platform import system
from time import time
from floop.util.termcolor import termcolor, cprint 
from floop.device.device import build, create, destroy, ps, push, run, test, \
        DeviceSourceDirectoryNotFound, \
        DeviceBuildException, \
        DeviceRunException, \
        DeviceTestException, \
        DeviceCommunicationException, \
        DevicePSException
from .config import Config, ConfigFileDoesNotExist, SourceDirectoryDoesNotExist, MalformedConfigException, UnmetHostDependencyException, RedundantDeviceConfigException

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
    '''
    Provided CLI commands and flags cannot be used together
    '''
    pass

def quiet():
    '''
    Remove console handler from logger to prevent printing to stdout

    This is a convenience function that you can use for defining
    verbose flags for CLI commands. If the flag is present, do nothing.
    If the -v flag is absent, then call quiet() inside of the method.
    '''
    log = logging.getLogger()
    for handler in log.handlers[:]:
        if handler.name == 'console':
            log.removeHandler(handler)

class FloopCLI(object):
    '''
    CLI entry point, handles all CLI calls

    Parses all CLI commands then calls the appropriate
    class method matching the CLI commands

    Attributes:
        config (:py:class:`floop.config.Config`):  
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
        parser.add_argument('--version',
                help='Print floop CLI version',
                action='store_true')
        # handle --version flag
        if len(argv) == 2 and argv[-1] == '--version':
            args = parser.parse_args(argv[1:])
            if args.version:
                try:
                    version = require('floop-cli')[0].version
                    print(version)
                    exit(0)
                except DistributionNotFound:
                    exit('''Error| pip package "floop-cli" is not installed\n\n
\tOptions to fix this error:\n\
\t--------------------------\n\
\tInstall floop via pip: pip install floop
''')
        parser.add_argument('-c', '--config-file', 
                help='Specify a non-default configuration file')
        parser.add_argument('command', help='Subcommand to run')
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
        except ConfigFileDoesNotExist:
            exit('Error| floop config file not found: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCopy an existing floop config file to the default path: {}\n\
\tGenerate a default config file by running: floop config\n\
\tUse the -c flag to point to a non-default config file: floop -c your-config-file.json'.format(
    config_file, _FLOOP_CONFIG_DEFAULT_FILE))
        except (SourceDirectoryDoesNotExist, DeviceSourceDirectoryNotFound):
            exit('''Error| Cannot find host_source_directory in config file: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tMake a new host_source_directory and define it in config file\n\
\tChange host_source_directory in config file to a valid filepath\n\
\tMake sure you have permission to access the files in host_source_directory'''.format(config_file))
        except RedundantDeviceConfigException as e:
            exit('''Error| Redundant address or name for devices in config: {} in {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tEdit config file so all device names and addresses are unique\n\
'''.format(str(e), config_file))
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
        except DeviceBuildException as e:
            exit('''Error| Build on target device returned non-zero error\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCheck floop logs for this device: floop logs -m device-name\n\
''')
        except DeviceRunException as e:
            exit('''Error| Run on target device returned non-zero error\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCheck floop logs for this device: floop logs -m device-name\n\
''')
        except DeviceTestException as e:
            exit('''Error| Test on target device returned non-zero error\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCheck floop logs for this device: floop logs -m device-name\n\
''')
        except DeviceCommunicationException as e:
            exit('''Error| Communication with target device returned non-zero error\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCheck that you have Internet access from the host\n\
\tCheck that the device is still accessible at the address in your config file\n\
''')
        except DevicePSException as e:
            exit('''Error| ps on target device returned non-zero error\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCheck that you have Internet access from the host\n\
\tCheck that the device is still accessible at the address in your config file\n\
\tTry to re-create the target device: floop create\n\
''')

    def __cprint(self, string, color=termcolor.DEFAULT):
        '''
        Wrapper for internal color print

        Args:
            string (str): 
                string to print
            color (str):
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
        '''
        Create new Docker Machines for each device in the configuration
        '''
        parser = argparse.ArgumentParser(
                description='Initialize single project communication between host and device(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        with Pool() as pool:
            pool.map(create, self.devices)

    def ps(self):
        '''
        Show running applications and tests on all targets
        '''
        # TODO: add metrics command to get resource usage info AND process info
        parser = argparse.ArgumentParser(
                description='List all initiated device(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        print('ps...')
        with Pool() as pool:
            pool.map(ps, self.devices)
     
    def logs(self):
        '''
        Print target logs to the host console
        '''
        # TODO: add -f option (bonus if it's pipe-able)
        parser = argparse.ArgumentParser(
                description='Logs from initialized device(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        parser.add_argument('-m', '--match',
                help='Print lines that contain the match term')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        print('logs...')
        with open('floop.log') as log:
            for line in log.readlines():
                if args.match is not None:
                    if args.match in line:
                        print(line, end="")
                elif not line == '\n':
                    print(line, end="")

    def push(self):
        '''
        Push code from host to all targets

        Automatically synchronizes code between host and targets.
        If you delete a file in the host source, then that file will
        be deleted on all targets.
        '''
        # TODO: add .floopignore ?
        parser = argparse.ArgumentParser(
                description='Push code from host to device(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        print('push...')
        with Pool() as pool:
            pool.map(
                    partial(push,
                        source_directory=self.source_directory,
                        target_directory=self.target_directory),
                    self.devices)

    def build(self):
        '''
        Build code on all targets, using Dockerfile in source directory

        Automatically performs a push before building in
        order to ensure that the host and targets have
        the same code.
        '''
        # TODO: add -v command to tee build outputs to logs AND local stdout
        parser = argparse.ArgumentParser(
                description='Build code on device(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        print('build...')
        #self.push()
        with Pool() as pool:
            pool.map(
                    partial(build,
                        source_directory=self.source_directory,
                        target_directory=self.target_directory),
                    self.devices)

    def run(self):
        '''
        Run code on all targets, using Dockerfile in source directory

        Automatically performs a push and a build
        in order to ensure that the host and targets
        have the same code.
        '''
        # TODO: add -v command to tee build outputs to logs AND local stdout
        parser = argparse.ArgumentParser(
                description='Run code on device(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        print('run...')
        with Pool()as pool:
            pool.map(
                    partial(run,
                        source_directory=self.source_directory,
                        target_directory=self.target_directory),
                    self.devices)
                
    def test(self):
        '''
        Test code on all targets, using Dockerfile.test in source directory

        Automatically performs a push and a build
        in order to ensure that the host and targets
        have the same code.
        '''
        # TODO: check that test YAML exists
        parser = argparse.ArgumentParser(
                description='Test code on device(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        print('test...')
        test_command = 'docker build'
        with Pool()as pool:
            pool.map(
                    partial(test,
                        source_directory=self.source_directory,
                        target_directory=self.target_directory),
                    self.devices)

    def destroy(self):
        '''
        Destroy project, code, and environment on all targets

        Does not remove local source code, builds, test, or logs.
        '''
        parser = argparse.ArgumentParser(
                description='Destroy project, code, and environment on device(s) but not host')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        print('clean...')
        with Pool() as pool:
            pool.map(destroy, self.devices)
