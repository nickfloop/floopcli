import logging
import sys
import pytest

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

class DeviceCreateException(Exception):
    '''
    Non-zero exit code while creating new Docker machine
    '''
    pass

class DockerMachineBinaryNotFound(Exception):
    '''
    Specified docker-machine binary does not exist
    '''
    pass

class DeviceSourceDirectoryNotFound(Exception):
    '''
    Specified target source code directory does not exist
    '''
    pass

class DeviceBuildFileNotFound(Exception):
    '''
    Host source code has no Dockerfile
    '''
    pass

class DeviceTestFileNotFound(Exception):
    '''
    Host source code has no Dockerfile.test
    '''
    pass

class DeviceCommunicationException(Exception):
    '''
    Cannot communicate with device via docker-machine SSH
    '''
    pass

class DeviceBuildException(Exception):
    '''
    Target device build command returned non-zero exit code
    '''
    pass
class DeviceRunException(Exception):
    '''
    Target device run command returned non-zero exit code
    '''
    pass

class DeviceTestException(Exception):
    '''
    Target device test command returned non-zero exit code
    '''
    pass

class DeviceDestroyException(Exception):
    '''
    Target device destroy command returned non-zero exit code
    '''
    pass

class DevicePSException(Exception):
    '''
    Target device ps command returned non-zero exit code
    '''
    pass

class Device(object):
    '''
    Handles initializing and interacting with a target device

    All attributes are immutable. If you try to set an instance
    attribute after initialize, it will raise :py:class:`CannotSetImmutableAttribute`

    Args:
        address (str):
            Device IP address (reachable by SSH)
        docker_machine_bin (str):
            Full path to docker-machine binary
        name (str):
            Device name (must match Docker machine name)
        ssh_key (str):
            Path of SSH private key on host that corresponds to target device
        user (str):
            Device SSH user
    '''
    def __init__(self,
            address: str,
            docker_machine_bin: str,
            name: str,
            ssh_key: str,
            user: str) -> None:

        self.docker_machine_bin = docker_machine_bin
        '''Full path to docker-machine binary'''
        self.address = address
        '''Device IP address (reachable by SSH)'''
        self.name = name.replace(' ','').replace('-','')
        '''Device name (must match Docker machine name, if machine already exist)
        
        During initialization, all machine names will have spaces and -'s removed
        '''
        self.ssh_key = ssh_key
        '''Path of SSH private key on host that corresponds to target device'''
        self.user = user
        '''Device SSH user'''

    @property
    def address(self) -> str:
        return self.__address

    @address.setter
    def address(self, value: str) -> None:
        if not hasattr(self, 'address'):
            self.__address = value
        else:
            raise CannotSetImmutableAttribute('address')

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if not hasattr(self, 'name'):
            self.__name = value
        else:
            raise CannotSetImmutableAttribute('name')

    @property
    def ssh_key(self) -> str:
        return self.__ssh_key

    @ssh_key.setter
    def ssh_key(self, value: str) -> None:
        '''
        SSH key setter

        Args:
            value (str):
                full path of SSH private key for device
        Raises:
            :py:class:`floop.device.device.SSHKeyNotFound`:
                SSH private key file does not exist
            :py:class:`floop.device.device.CannotSetImmutableAttribute`:
                attempting to modify the ssh_key attribute after initialization will fail
        '''
        value = expanduser(value)
        if not hasattr(self, 'ssh_key'):
            if not isfile(value):
                raise SSHKeyNotFound(value)
            self.__ssh_key = value
        else:
            raise CannotSetImmutableAttribute('ssh_key')

    @property
    def user(self) -> str:
        return self.__user

    @user.setter
    def user(self, value: str) -> None:
        '''
        SSH user setter

        Args:
            value (str):
                name of SSH user for device
        Raises:
            :py:class:`floop.device.device.CannotSetImmutableAttribute`:
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
        Run docker-machine SSH command on target device

        Args:
            command (str):
                command to run on target device
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
            self.docker_machine_bin, self.name, command)
        out, err = syscall(sys_string, check=check, verbose=verbose)
        return out

def __log(device: Device, level: str, message: str) -> None:
    '''
    Log message about device to default logger

    Automatically prepends calling function name to
    log output

    Args:
        device (:py:class:`floop.device.device.Device`):
            initialized target device object
        level (str):
            logger logging level (only use 'info' or 'error')
        message (str):
            message to log
    '''
    if hasattr(logger, level):
        message = '{} (target) - {}: {}'.format(
                device.name,
                sys._getframe(1).f_code.co_name,
                message)
        getattr(logger, level)(message)

###  parallelizable methods that act on Device objects
# these functions are pickle-able, but class methods are NOT
# so these functions can be passed to multiprocessing.Pool
def create(device: Device, check: bool=True) -> None:
    '''
    Parallelizable; create new docker-machine on target device

    Args:
        device (:py:class:`floop.device.device.Device`):
            initialized target device object
        check (bool):
            if True, check device creation succeeded by running
            'pwd' via docker-machine SSH on newly created device
    Raises:
        :py:class:`floop.device.device.DeviceCreateException`:
            device creation failed during docker-machine create or
            'pwd' check failed
    '''
    create_command = '{} create --driver generic --generic-ip-address {} --generic-ssh-user {} --generic-ssh-key {} --engine-storage-driver overlay {}'.format(
        device.docker_machine_bin,
        device.address, 
        device.user, 
        device.ssh_key, 
        device.name)
    __log(device, 'info', create_command)
    try:
        out, _ = syscall(create_command, check=False)
        __log(device, 'info', out)
        if check:
            check_command = 'pwd'
            __log(device, 'info', 'Checking with {}'.format(check_command))
            outd = device.run_ssh_command('pwd', check=check)
            __log(device, 'info', outd)
    except SystemCallException as e:
        force_destroy_command = '{0} rm -f {1}'.format(device.docker_machine_bin, device.name)
        __log(device, 
                'error',
                'Cleaning up failed docker machine: {}'.format(
                    force_destroy_command))
        out = syscall(force_destroy_command, check=False)
        __log(device, 'error', out)
        __log(device, 'error', str(e))
        raise DeviceCreateException(str(e))

def push(device: Device,
        source_directory: str,
        target_directory: str,
        check: bool=True) -> None:
    '''
    Parallelizable; push files from host to target device 

    Args:
        device (:py:class:`floop.device.device.Device`):
            initialized target device object
        source_directory (str):
            full path host source code directory on host
        target_directory (str):
            full path of source code directory on target device
        check (bool):
            if True, check device creation succeeded by running
            'pwd' via docker-machine SSH on newly created device
    Raises:
        :py:class:`floop.device.device.DeviceCreateException`:
            device creation failed during docker-machine create or
            'pwd' check failed
    '''
    # prevents race condition where source exists at start of floop
    # call but gets removed before push 
    if not isdir(source_directory):
        __log(device, 'error', 'Source directory not found: {}'.format(source_directory))
        raise DeviceSourceDirectoryNotFound(source_directory)
    try:
        mkdir_string = 'mkdir -p {}'.format(target_directory)
        __log(device, 'info', mkdir_string)
        out = device.run_ssh_command(mkdir_string, check=True)
        __log(device, 'info', out)
        sync_string = "rsync -avz -e '{} ssh' {} {}:'{}' --delete".format(device.docker_machine_bin, source_directory,
            device.name, target_directory)
        __log(device, 'info', sync_string)
        out, err = syscall(sync_string, check=check)
        __log(device, 'info', out)
    except SystemCallException as e:
        __log(device, 'error', str(e))
        raise DeviceCommunicationException(str(e))

def build(device: Device,
        source_directory: str, target_directory: str,
        check: bool=True) -> None:
    '''
    Parallelizable; push then build files from host on target device 

    Args:
        device (:py:class:`floop.device.device.Device`):
            initialized target device object
        source_directory (str):
            full path host source code directory on host
        target_directory (str):
            full path of source code directory on target device
            
        check (bool):
            if True, check device creation succeeded by running
            'pwd' via docker-machine SSH on newly created device
    Raises:
        :py:class:`DeviceBuildFileNotFound`:
            no Dockerfile in source code directory on host
        :py:class:`floop.device.device.DeviceBuildException`:
            build commands returned non-zero exit code
    '''

    build_file = '{}/Dockerfile'.format(source_directory)
    if not isfile(build_file):
        __log(device, 'error', 'Device build file not found: {}'.format(build_file))
        raise DeviceBuildFileNotFound(build_file)
    push(device=device,source_directory=source_directory, target_directory=target_directory)
    meta_build_command = 'docker build -t floop {}/'.format(target_directory)
    __log(device, 'info', meta_build_command)
    try:
        out = device.run_ssh_command(meta_build_command, check=check)
        __log(device, 'info', out)
    except SystemCallException as e:
        __log(device, 'error', str(e))
        raise DeviceBuildException(str(e))

def run(device: Device,
        source_directory: str,
        target_directory: str,
        check: bool=True,
        verbose: bool=False) -> None:
    '''
    Parallelizable; push, build, then run files from host on target device 

    Args:
        device (:py:class:`floop.device.device.Device`):
            initialized target device object
        source_directory (str):
            full path host source code directory on host
        target_directory (str):
            full path of source code directory on target device
        check (bool):
            if True, check device creation succeeded by running
            'pwd' via docker-machine SSH on newly created device
    Raises:
        :py:class:`DeviceCommunicationException`:
            could not communicate from host to device to remove runtime container
        :py:class:`floop.device.device.DeviceRunException`:
            run commands returned non-zero exit code
    '''

    build(device=device,source_directory=source_directory, target_directory=target_directory)
    rm_command = 'docker rm -f floop || true'
    __log(device, 'info', rm_command)
    try:
        out = device.run_ssh_command(command=rm_command, check=check, verbose=verbose)
        __log(device, 'info', out)
        run_command = 'docker run --name floop -v {}:/floop/ floop'.format(
                target_directory)
        __log(device, 'info', run_command)
        out = device.run_ssh_command(command=run_command, check=check, verbose=verbose)
        __log(device, 'info', out)
    except SystemCallException as e:
        __log(device, 'error', str(e))
        raise DeviceRunException(str(e))

def ps(device: Device,
        check: bool=True) -> None:
    '''
    Parallelizable; push, build, then run files from host on target device 

    Args:
        device (:py:class:`floop.device.device.Device`):
            initialized target device object
        check (bool):
            if True, check device creation succeeded by running
            'pwd' via docker-machine SSH on newly created device
    Raises:
        :py:class:`floop.device.device.DevicePSException`:
            ps commands returned non-zero exit code
    '''

    ps_command = 'docker ps'
    __log(device, 'info', ps_command)
    try:
        out = device.run_ssh_command(ps_command, check=check)
        __log(device, 'info', out)
    # TODO: find a case where device initializes but ps fails
    except SystemCallException as e:
        __log(device, 'error', str(e))
        raise DevicePSException(str(e))

# pytest thinks this is a test!
@pytest.mark.skip(reason='Not actually a test!')
def test(device: Device,
        source_directory: str,
        target_directory: str,
        check: bool=True) -> None:
    '''
    Parallelizable; push, build, then run test files from host on target device 

    Args:
        device (:py:class:`floop.device.device.Device`):
            initialized target device object
        source_directory (str):
            full path host source code directory on host
        target_directory (str):
            full path of source code directory on target device
        check (bool):
            if True, check device creation succeeded by running
            'pwd' via docker-machine SSH on newly created device
    Raises:
        :py:class:`DeviceTestFileNotFound`:
            no Dockerfile.test in source code directory on host
        :py:class:`floop.device.device.DeviceTestException`:
            test commands returned non-zero exit code
    '''
    test_file = '{}/Dockerfile.test'.format(source_directory)
    if not isfile(test_file):
        __log(device, 'error', 'Test file not found: {}'.format(test_file))
        raise DeviceTestFileNotFound(test_file)
    push(device=device, source_directory=source_directory, target_directory=target_directory)
    try:
        rm_command = 'docker rm -f flooptest || true'
        __log(device, 'info', rm_command)
        out = device.run_ssh_command(rm_command, check=check)
        __log(device, 'info', out)
        test_build_command = 'docker build -t flooptest -f {}/{} {}'.format(
                target_directory, test_file.split('/')[-1], target_directory)
        __log(device, 'info', test_build_command)
        out = device.run_ssh_command(test_build_command, check=check)
        __log(device, 'info', out)
        test_run_command = 'docker run --name flooptest -v {}:/floop/ flooptest'.format(
                target_directory)
        __log(device, 'info', test_run_command)
        out = device.run_ssh_command(test_run_command, check=check)
        __log(device, 'info', out)
    except SystemCallException as e:
        __log(device, 'error', str(e))
        raise DeviceTestException(str(e))

def destroy(device: Device,
        target_directory: str,
        check: bool=True) -> None:
    '''
    Parallelizable; destroy device by uninstalling docker and rm'ing Docker machine

    Args:
        device (:py:class:`floop.device.device.Device`):
            initialized target device object
        target_directory (str):
            full path of source code directory on target device
        check (bool):
            if True, check that device destroy system calls
            return non-zero exit codes
    Raises:
        :py:class:`floop.device.device.DeviceDestroyException`:
            destroy commands returned non-zero exit code
    '''
    try:
        # can call docker-machine ssh commands or syscall commands 
        rm_target_source = ('ssh', 'rm -rf {}'.format(target_directory))
        uninstall_docker = ('ssh', 'sudo apt-get purge -y docker-ce || true')
        rm_device = ('sys', '{} rm -f {}'.format(
            device.docker_machine_bin, device.name))
        # order matters
        commands = [
                rm_target_source,
                uninstall_docker,
                rm_device
                ]
        for command in commands:
            kind, command = command
            __log(device, 'info', command)
            if kind == 'ssh':
                out = device.run_ssh_command(command=command, check=check)
                __log(device, 'info', out)
            elif kind =='sys':
                out = syscall(command=command, check=check)
                __log(device, 'info', out)
    # TODO: find a case where init succeeds but destroy fails, enforce idempotency
    except SystemCallException as e:
        __log(device, 'error', str(e))
        raise DeviceDestroyException(str(e))
