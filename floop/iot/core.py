import logging
import sys
import pytest
import os

from subprocess import check_output
from os.path import isfile, isdir, expanduser
from floop.util.syscall import syscall, SystemCallException

logger = logging.getLogger(__name__)

class CannotSetImmutableAttribute(Exception):
    '''
    Tried to set immutable attribute after initialization
    '''
    pass

class SSHKeyNotFound(Exception):
    '''
    Specified SSH private key file does not exist
    '''
    pass

class CoreCreateException(Exception):
    '''
    Non-zero exit code while creating new Docker machine
    '''
    pass

class DockerMachineBinaryNotFound(Exception):
    '''
    Specified docker-machine binary does not exist
    '''
    pass

class CoreSourceNotFound(Exception):
    '''
    Specified target source code directory does not exist
    '''
    pass

class CoreBuildFileNotFound(Exception):
    '''
    Host source code has no Dockerfile
    '''
    pass

class CoreTestFileNotFound(Exception):
    '''
    Host source code has no Dockerfile.test
    '''
    pass

class CoreCommunicationException(Exception):
    '''
    Cannot communicate with core via docker-machine SSH
    '''
    pass

class CoreBuildException(Exception):
    '''
    Target core build command returned non-zero exit code
    '''
    pass
class CoreRunException(Exception):
    '''
    Target core run command returned non-zero exit code
    '''
    pass

class CoreTestException(Exception):
    '''
    Target core test command returned non-zero exit code
    '''
    pass

class CoreDestroyException(Exception):
    '''
    Target core destroy command returned non-zero exit code
    '''
    pass

class CorePSException(Exception):
    '''
    Target core ps command returned non-zero exit code
    '''
    pass

class Core(object):
    '''
    Handles initializing and interacting with a target core

    All attributes are immutable. If you try to set an instance
    attribute after initialize, it will raise :py:class:`CannotSetImmutableAttribute`

    Args:
        address (str):
            Core IP address (reachable by SSH)
        host_docker_machine_bin (str):
            Full path to docker-machine binary
        core (str):
            Core core (must match Docker machine core)
        ssh_key (str):
            Path of SSH private key on host that corresponds to target core
        user (str):
            Core SSH user
    '''
    def __init__(self,
            address: str,
            target_source: str,
            group: str,
            host_docker_machine_bin: str,
            host_key: str,
            host_rsync_bin: str,
            host_source: str,
            core: str,
            user: str,
            **kwargs: str) -> None:

        self.address = address
        '''Core IP address (reachable by SSH)'''
        self.target_source = target_source
        '''Directory on the target operating system to store files'''
        self.group = group
        '''Core group core'''
        self.host_docker_machine_bin = host_docker_machine_bin
        '''Path on host to docker-machine binary'''
        self.host_key = host_key
        '''Path on host to SSH key that works for user'''
        self.host_rsync_bin = host_rsync_bin
        '''Path on host to rsync binary'''
        self.host_source = host_source
        '''Path on host to source file directory'''
        self.core = core.replace(' ','').replace('-','')
        '''Core core (must match Docker machine core, if machine already exist)
        During initialization, all machine cores will have spaces and -'s removed
        '''
        self.user = user
        '''Core SSH user on the target'''

    @property
    def address(self) -> str:
        return self.__address

    @address.setter
    def address(self, value: str) -> None:
        if hasattr(self, 'address'):
            raise CannotSetImmutableAttribute('address')
        self.__address = value

    @property
    def target_source(self) -> str:
        return self.__target_source

    @target_source.setter
    def target_source(self, value: str) -> None:
        if hasattr(self, 'target_source'):
            raise CannotSetImmutableAttribute('target_source')
        self.__target_source = value

    @property
    def group(self) -> str:
        return self.__group

    @group.setter
    def group(self, value: str) -> None:
        if hasattr(self, 'group'):
            raise CannotSetImmutableAttribute('group')
        self.__group = value

    @property
    def host_docker_machine_bin(self) -> str:
        return self.__host_docker_machine_bin

    @host_docker_machine_bin.setter
    def host_docker_machine_bin(self, value: str) -> None:
        if hasattr(self, 'host_docker_machine_bin'):
            raise CannotSetImmutableAttribute('host_docker_machine_bin')
        self.__host_docker_machine_bin = value

    @property
    def host_key(self) -> str:
        return self.__host_key

    @host_key.setter
    def host_key(self, value: str) -> None:
        '''
        SSH key setter

        Args:
            value (str):
                path of SSH private key for core
        Raises:
            :py:class:`floop.core.core.SSHKeyNotFound`:
                SSH private key file does not exist
            :py:class:`floop.core.core.CannotSetImmutableAttribute`:
                attempting to modify the host_key attribute after initialization will fail
        '''
        value = expanduser(value)
        if hasattr(self, 'host_key'):
            raise CannotSetImmutableAttribute('host_key')
        if not isfile(value) or value is None:
            raise SSHKeyNotFound(value)
        self.__host_key = value

    @property
    def host_rsync_bin(self) -> str:
        return self.__host_rsync_bin

    @host_rsync_bin.setter
    def host_rsync_bin(self, value: str) -> None:
        if hasattr(self, 'host_rsync_bin'):
            raise CannotSetImmutableAttribute('host_rsync_bin')
        self.__host_rsync_bin = value

    @property
    def host_source(self) -> str:
        return self.__host_source

    @host_source.setter
    def host_source(self, value: str) -> None:
        if hasattr(self, 'host_source'):
            raise CannotSetImmutableAttribute('host_source')
        if not isdir(value):
            raise CoreSourceNotFound(value)
        self.__host_source = value

    @property
    def core(self) -> str:
        return self.__core

    @core.setter
    def core(self, value: str) -> None:
        if hasattr(self, 'core'):
            raise CannotSetImmutableAttribute('core')
        self.__core = value

    @property
    def user(self) -> str:
        return self.__user

    @user.setter
    def user(self, value: str) -> None:
        '''
        SSH user setter

        Args:
            value (str):
                core of SSH user for core
        Raises:
            :py:class:`floop.core.core.CannotSetImmutableAttribute`:
                attempting to modify the user attribute after initialization will fail
        '''

        if not hasattr(self, 'user'):
            self.__user = value
        else:
            raise CannotSetImmutableAttribute('user')

    def run_ssh_command(self,
            command: str,
            check: bool=True,
            verbose: bool=False) -> str:
        '''
        Run docker-machine SSH command on target core

        Args:
            command (str):
                command to run on target core
            check (bool):
                if True, check whether command exit code is non-zero
        Returns:
            str:
                stdout output of SSH command
        Raises:
            :py:class:`floop.util.syscall.SystemCallException`:
                SSH command exit code was non-zero
        '''
        sys_string = '{} ssh {} {}'.format(
            self.host_docker_machine_bin, self.core, command)
        out, err = syscall(sys_string, check=check, verbose=verbose)
        return out

def __log(core: Core, level: str, message: str) -> None:
    '''
    Log message about core to default logger

    Automatically prepends calling function core to
    log output

    Args:
        core (:py:class:`floop.core.core.Core`):
            initialized target core object
        level (str):
            logger logging level (only use 'info' or 'error')
        message (str):
            message to log
    '''
    if hasattr(logger, level):
        message = '{} (target) - {}: {}'.format(
                core.core,
                sys._getframe(1).f_code.co_name,
                message)
        getattr(logger, level)(message)

###  parallelizable methods that act on Core objects
# these functions are pickle-able, but class methods are NOT
# so these functions can be passed to multiprocessing.Pool
def create(core: Core, check: bool=True) -> None:
    '''
    Parallelizable; create new docker-machine on target core

    Args:
        core (:py:class:`floop.core.core.Core`):
            initialized target core object
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
    Raises:
        :py:class:`floop.core.core.CoreCreateException`:
            core creation failed during docker-machine create or
            'pwd' check failed
    '''
    create_command = '{} create --driver generic --generic-ip-address {} --generic-ssh-user {} --generic-ssh-key {} --engine-storage-driver overlay {}'.format(
        core.host_docker_machine_bin,
        core.address, 
        core.user, 
        core.host_key, 
        core.core)
    __log(core, 'info', create_command)
    try:
        out, _ = syscall(create_command, check=False)
        __log(core, 'info', out)
        if check:
            check_command = 'pwd'
            __log(core, 'info', 'Checking with {}'.format(check_command))
            outd = core.run_ssh_command('pwd', check=check)
            __log(core, 'info', outd)
    except SystemCallException as e:
        force_destroy_command = '{0} rm -f {1}'.format(core.host_docker_machine_bin, core.core)
        __log(core, 
                'error',
                'Cleaning up failed docker machine: {}'.format(
                    force_destroy_command))
        out, err = syscall(force_destroy_command, check=False)
        __log(core, 'error', str((out, err)))
        __log(core, 'error', str(e))
        raise CoreCreateException(str(e))

def push(core: Core, check: bool=True) -> None:
    '''
    Parallelizable; push files from host to target core 

    Args:
        core (:py:class:`floop.core.core.Core`):
            initialized target core object
        core.target_source (str):
            full path host source code directory on host
        core.target_source (str):
            full path of source code directory on target core
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
    Raises:
        :py:class:`floop.core.core.CoreCreateException`:
            core creation failed during docker-machine create or
            'pwd' check failed
    '''
    # prevents race condition where source exists at start of floop
    # call but gets removed before push 
    # TODO: simulate the race condition
    if not isdir(core.host_source):
        __log(core, 'error', 'Source not found: {}'.format(core.host_source))
        raise CoreSourceNotFound(core.host_source)
    try:
        mkdir_string = 'mkdir -p {}'.format(core.target_source)
        __log(core, 'info', mkdir_string)
        out = core.run_ssh_command(mkdir_string, check=True)
        __log(core, 'info', out)
        sync_string = "rsync -avz -e '{} ssh' {} {}:'{}' --delete".format(core.host_docker_machine_bin, core.host_source,
            core.core, core.target_source)
        __log(core, 'info', sync_string)
        out, err = syscall(sync_string, check=check)
        __log(core, 'info', out)
    except SystemCallException as e:
        __log(core, 'error', str(e))
        raise CoreCommunicationException(str(e))

def build(core: Core, check: bool=True) -> None:
    '''
    Parallelizable; push then build files from host on target core 

    Args:
        core (:py:class:`floop.core.core.Core`):
            initialized target core object
            
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
    Raises:
        :py:class:`CoreBuildFileNotFound`:
            no Dockerfile in source code directory on host
        :py:class:`floop.core.core.CoreBuildException`:
            build commands returned non-zero exit code
    '''

    build_file = '{}/Dockerfile'.format(core.host_source)
    if not isfile(build_file) or build_file is None:
        __log(core, 'error', 'Core build file not found: {}'.format(build_file))
        raise CoreBuildFileNotFound(build_file)
    push(core)
    meta_build_command = 'docker build -t floop {}/'.format(core.target_source)
    __log(core, 'info', meta_build_command)
    try:
        out = core.run_ssh_command(meta_build_command, check=check)
        __log(core, 'info', out)
    except SystemCallException as e:
        __log(core, 'error', str(e))
        raise CoreBuildException(str(e))

def run(core: Core,
        check: bool=True,
        verbose: bool=False) -> None:
    '''
    Parallelizable; push, build, then run files from host on target core 

    Args:
        core (:py:class:`floop.core.core.Core`):
            initialized target core object
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
    Raises:
        :py:class:`CoreCommunicationException`:
            could not communicate from host to core to remove runtime container
        :py:class:`floop.core.core.CoreRunException`:
            run commands returned non-zero exit code
    '''

    build(core)
    rm_command = 'docker rm -f floop || true'
    __log(core, 'info', rm_command)
    try:
        out = core.run_ssh_command(command=rm_command, check=check, verbose=verbose)
        __log(core, 'info', out)
        run_command = 'docker run --name floop -v {}:/floop/ floop'.format(
                core.target_source)
        __log(core, 'info', run_command)
        out = core.run_ssh_command(command=run_command, check=check, verbose=verbose)
        __log(core, 'info', out)
    except SystemCallException as e:
        __log(core, 'error', str(e))
        raise CoreRunException(str(e))

def ps(core: Core,
        check: bool=True) -> None:
    '''
    Parallelizable; push, build, then run files from host on target core 

    Args:
        core (:py:class:`floop.core.core.Core`):
            initialized target core object
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
    Raises:
        :py:class:`floop.core.core.CorePSException`:
            ps commands returned non-zero exit code
    '''

    ps_command = 'docker ps'
    __log(core, 'info', ps_command)
    try:
        out = core.run_ssh_command(ps_command, check=check)
        __log(core, 'info', out)
    # TODO: find a case where core initializes but ps fails
    except SystemCallException as e:
        __log(core, 'error', str(e))
        raise CorePSException(str(e))

# pytest thinks this is a test!
@pytest.mark.skip(reason='Not actually a test!')
def test(core: Core,
        check: bool=True) -> None:
    '''
    Parallelizable; push, build, then run test files from host on target core 

    Args:
        core (:py:class:`floop.core.core.Core`):
            initialized target core object
        core.target_source (str):
            full path host source code directory on host
        core.target_source (str):
            full path of source code directory on target core
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
    Raises:
        :py:class:`CoreTestFileNotFound`:
            no Dockerfile.test in source code directory on host
        :py:class:`floop.core.core.CoreTestException`:
            test commands returned non-zero exit code
    '''
    test_file = '{}/Dockerfile.test'.format(core.host_source)
    if not isfile(test_file) or test_file is None:
        __log(core, 'error', 'Test file not found: {}'.format(test_file))
        raise CoreTestFileNotFound(test_file)
    push(core)
    try:
        rm_command = 'docker rm -f flooptest || true'
        __log(core, 'info', rm_command)
        out = core.run_ssh_command(rm_command, check=check)
        __log(core, 'info', out)
        test_build_command = 'docker build -t flooptest -f {}/{} {}'.format(
                core.target_source, test_file.split('/')[-1], core.target_source)
        __log(core, 'info', test_build_command)
        out = core.run_ssh_command(test_build_command, check=check)
        __log(core, 'info', out)
        test_run_command = 'docker run --name flooptest -v {}:/floop/ flooptest'.format(
                core.target_source)
        __log(core, 'info', test_run_command)
        out = core.run_ssh_command(test_run_command, check=check)
        __log(core, 'info', out)
    except SystemCallException as e:
        __log(core, 'error', str(e))
        raise CoreTestException(str(e))

def destroy(core: Core,
        check: bool=True) -> None:
    '''
    Parallelizable; destroy core by uninstalling docker and rm'ing Docker machine

    Args:
        core (:py:class:`floop.core.core.Core`):
            initialized target core object
        core.target_source (str):
            full path of source code directory on target core
        check (bool):
            if True, check that core destroy system calls
            return non-zero exit codes
    Raises:
        :py:class:`floop.core.core.CoreDestroyException`:
            destroy commands returned non-zero exit code
    '''
    try:
        # can call docker-machine ssh commands or syscall commands 
        rm_target_source = ('ssh', 'rm -rf {}'.format(core.target_source))
        uninstall_docker = ('ssh', 'sudo apt-get purge -y docker-ce || true')
        rm_core = ('sys', '{} rm -f {}'.format(
            core.host_docker_machine_bin, core.core))
        # order matters
        commands = [
                rm_target_source,
                uninstall_docker,
                rm_core
                ]
        for command_ in commands:
            kind, command = command_
            __log(core, 'info', command)
            if kind == 'ssh':
                out = core.run_ssh_command(command=command, check=check)
                __log(core, 'info', out)
            elif kind =='sys':
                out, err = syscall(command=command, check=check)
                __log(core, 'info', str((out, err)))
    # TODO: find a case where init succeeds but destroy fails, enforce idempotency
    except SystemCallException as e:
        __log(core, 'error', str(e))
        raise CoreDestroyException(str(e))
