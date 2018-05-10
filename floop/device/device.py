import logging
import sys
import pytest

from subprocess import check_output
from os.path import isfile, isdir, expanduser
from floop.util.syscall import syscall, SystemCallException

logger = logging.getLogger(__name__)

class CannotSetImmutableAttributeException(Exception):
    pass

class CannotFindSSHKeyException(Exception):
    pass

class DockerMachineCreateException(Exception):
    pass

class CannotFindDockerMachineBinary(Exception):
    pass

class DeviceSourceDirectoryDoesNotExist(Exception):
    pass

class DeviceBuildFileNotFound(Exception):
    pass

class DeviceTestFileNotFound(Exception):
    pass

class DeviceCommunicationException(Exception):
    pass

class DeviceBuildException(Exception):
    pass

class Device(object):
    '''
    Handles initializing and interacting with a target device

    All attributes are immutable. If you try to set an instance
    attribute after initialize, it will raise :py:class:`CannotSetImmutableAttributeException`

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
        '''Device name (must match Docker machine name)'''
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
            raise CannotSetImmutableAttributeException('address')

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if not hasattr(self, 'name'):
            self.__name = value
        else:
            raise CannotSetImmutableAttributeException('name')

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
            :py:class:`floop.device.device.CannotFindSSHKeyException`:
                SSH private key file does not exist
            :py:class:`floop.device.device.CannotSetImmutableAttributeException`:
                attempting to modify the ssh_key attribute after initialization will fail
        '''
        value = expanduser(value)
        if not hasattr(self, 'ssh_key'):
            if not isfile(value):
                raise CannotFindSSHKeyException(value)
            self.__ssh_key = value
        else:
            raise CannotSetImmutableAttributeException('ssh_key')

    @property
    def user(self) -> str:
        return self.__user

    @user.setter
    def user(self, value: str) -> None:
        if not hasattr(self, 'user'):
            self.__user = value
        else:
            raise CannotSetImmutableAttributeException('user')

    def run_ssh_command(self, command: str, check: bool=True) -> None:
        '''
        Run docker-machine SSH command on target device

        Args:
            command (str):
                command to run on target device
            check (bool):
                if True, check whether command return code is non-zero
        Returns:
            str:
                stdout output of SSH command
        Raises:
            :py:class:`floop.util.syscall.SystemCallException`:
                SSH command return code was non-zero
        '''
        sys_string = '{} ssh {} {}'.format(
            self.docker_machine_bin, self.name, command)
        out, err = syscall(sys_string, check=check)
        return out.decode('utf-8')

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
        message = '{} - {}: {}'.format(
                device.name,
                sys._getframe(1).f_code.co_name,
                message)
        getattr(logger, level)(message)

###  parallelizable methods that act on Device objects
# these functions are pickle-able, but class methods are NOT
# so these functions can be passed to multiprocessing.Pool
def create(device, check=True) -> None:
    '''
    Parallelizable, create new docker-machine on target device

    Args:
        device (:py:class:`floop.device.device.Device`):
            initialized target device object
        check (bool):
            if True, check device creation succeeded by running
            'pwd' via docker-machine SSH on newly created device
    Raises:
        :py:class:`floop.device.device.DockerMachineCreateException`:
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
        __log(device, 'info', out.decode('utf-8'))
        if check:
            check_command = 'pwd'
            __log(device, 'info', 'Checking with {}'.format(check_command))
            out = device.run_ssh_command('pwd', check=check)
            __log(device, 'info', out)
    except SystemCallException as e:
        __log(device, 'error', str(e))
        raise DockerMachineCreateException(str(e))

def push(device,
        source_directory: str,
        target_directory: str,
        check: bool=True) -> str:
    # prevents race condition where source exists at start of floop
    # call but gets removed before push 
    if not isdir(source_directory):
        __log(device, 'error', 'Source directory not found: {}'.format(source_directory))
        raise DeviceSourceDirectoryDoesNotExist(source_directory)
    sys_string = "rsync -avz -e '{} ssh' {} {}:'{}' --delete".format(
        device.docker_machine_bin, source_directory,
        device.name, target_directory
        )
    __log(device, 'info', sys_string)
    try:
        out, err = syscall(sys_string, check=check)
        __log(device, 'info', out.decode('utf-8'))
    except SystemCallException as e:
        __log(device, 'error', str(e))
        raise DeviceCommunicationException(str(e))

def build(device, source_directory, target_directory, check=True):
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


def run(device, source_directory, target_directory, check=True):
    build(device=device,source_directory=source_directory, target_directory=target_directory)
    rm_command = 'docker rm -f floop || true'
    __log(device, 'info', rm_command)
    try:
        out = device.run_ssh_command(command=rm_command, check=check)
        __log(device, 'info', out)
    except SystemCallException as e:
        __log(device, 'error', str(e))
        raise DeviceCommunicationException(str(e))
    run_command = 'docker run --name floop -v {}:/floop/ floop'.format(
            target_directory)
    __log(device, 'info', run_command)
    try:
        out = device.run_ssh_command(command=run_command, check=check)
        __log(device, 'info', out)
    except SystemCallException as e:
        __log(device, 'error', str(e))
        raise DeviceRunException(str(e))

def ps(device, check=True):
    ps_command = 'docker ps'
    device.run_ssh_command(ps_command, check=check)

def logs(device, check=True):
    logs_command = 'docker logs floop'
    device.run_ssh_command(logs_command, check=check)

@pytest.mark.skip(reason='Not actually a test!')
def test(device, source_directory, target_directory, check=True):
    test_file = '{}/Dockerfile.test'.format(source_directory)
    if not isfile(test_file):
        raise DeviceTestFileNotFound(test_file)
    push(device=device, source_directory=source_directory, target_directory=target_directory)
    rm_command = 'docker rm -f flooptest || true'
    print(rm_command)
    device.run_ssh_command(rm_command, check=check)
    test_build_command = 'docker build -t flooptest -f {}/{} {}'.format(
            target_directory, test_file.split('/')[-1], target_directory)
    print(test_build_command)
    device.run_ssh_command(test_build_command, check=check)
    test_run_command = 'docker run --name flooptest -v {}:/floop/ flooptest'.format(
            target_directory)
    print(test_run_command)
    device.run_ssh_command(test_run_command, check=check)

def destroy(device, check=True):
    # TODO: delete source directory and rsync to clean up all device code
    uninstall_docker_command = "{} ssh {} 'sudo apt-get purge -y docker-ce'".format(device.docker_machine_bin, device.name)
    print(syscall(uninstall_docker_command, check=check))

