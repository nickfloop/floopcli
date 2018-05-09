from subprocess import check_output
from os.path import isfile, isdir, expanduser
from floop.util.syscall import syscall, SystemCallException

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

class Device(object):
    def __init__(self,
            address: str,
            docker_machine_bin: str,
            name: str,
            ssh_key: str,
            user: str) -> None:
        self.docker_machine_bin = docker_machine_bin
        self.address = address
        self.name = name.replace(' ','').replace('-','')
        self.ssh_key = ssh_key
        self.user = user

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

    def create(self) -> None:
        create_command = '{} create --driver generic --generic-ip-address {} --generic-ssh-user {} --generic-ssh-key {} --engine-storage-driver overlay {}'.format(
            self.docker_machine_bin,
            self.address, 
            self.user, 
            self.ssh_key, 
            self.name)
        print(create_command)
        out, err = syscall(create_command)
        if err is not None:
            raise DockerMachineCreateException(err)

    def build(self, source_directory, target_directory, check=True):
        build_file = '{}/Dockerfile'.format(source_directory)
        if not isfile(build_file):
            raise DeviceBuildFileNotFound(build_file)
        self.push(source_directory=source_directory, target_directory=target_directory)
        meta_build_command = 'docker build -t floop {}/'.format(target_directory)
        print(meta_build_command)
        self.run_ssh_command(meta_build_command, check=check)

    def test(self, source_directory, target_directory, check=True):
        test_file = '{}/Dockerfile.test'.format(source_directory)
        if not isfile(test_file):
            raise DeviceTestFileNotFound(test_file)
        self.push(source_directory=source_directory, target_directory=target_directory)
        test_build_command = 'docker build -t flooptest -f {}/{} {}'.format(
                target_directory, test_file.split('/')[-1], target_directory)
        print(test_build_command)
        self.run_ssh_command(test_build_command, check=check)
        test_run_command = 'docker run --name flooptest -v {}:/floop/ flooptest'.format(
                target_directory)
        print(test_run_command)
        self.run_ssh_command(test_run_command, check=check)

    def run_ssh_command(self, command: str, check: bool=False) -> None:
        print(syscall('{} ssh {} {}'.format(
            self.docker_machine_bin, self.name, command)
        , check))

    def push(self,
            source_directory: str,
            target_directory: str,
            check: bool=False) -> str:
        # prevents race condition where source exists at start of floop
        # call but gets removed before rsync
        if not isdir(source_directory):
            raise DeviceSourceDirectoryDoesNotExist(source_directory)
        sys_string = "rsync -avz -e '{} ssh' {} {}:'{}' --delete".format(
            self.docker_machine_bin, source_directory,
            self.name, target_directory
            )
        print(sys_string)
        out, err = syscall(sys_string, check=check)
        return (out, err)

    def destroy(self):
        # TODO: delete source directory and rsync to clean up all device code
        uninstall_docker_command = "{} ssh {} 'sudo apt-get purge -y docker-ce'".format(self.docker_machine_bin, self.name)
        print(syscall(uninstall_docker_command, check=True))

    def run(self, target_directory):
        rm_command = 'docker rm -f floop || true'
        print(rm_command)
        self.run_ssh_command(command=rm_command, check=True)
        run_command = 'docker run --name floop -v {}:/floop/ floop'.format(
                target_directory)
        print(run_command)
        self.run_ssh_command(command=run_command)

