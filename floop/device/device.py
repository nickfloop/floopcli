from subprocess import check_output
from os.path import isfile, expanduser
from floop.util.pipeline import pipeline

class CannotSetImmutableAttributeException(Exception):
    pass

class CannotFindSSHKeyException(Exception):
    pass

class DockerMachineCreateException(Exception):
    pass

class Device(object):
    def __init__(self, address: str, name: str, ssh_key: str, user: str) -> None:
        self.docker_machine_bin = '/usr/local/bin/docker-machine'
        self.address = address
        self.name = name
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
        out, err = pipeline(create_command)
        if err is not None:
            raise DockerMachineCreateException(err)

    def run_ssh_command(self, command: str) -> None:
        print(pipeline('{} ssh {} {}'.format(
            self.docker_machine_bin, self.name, command)
        ))

    def rsync(self,
            source_directory: str,
            target_directory: str) -> str:
        return pipeline("rsync -avz -e '{} ssh' {} {}:'{}' --delete".format(
            self.docker_machine_bin, source_directory,
            self.name, target_directory
            )
        )[0].decode('utf-8')

    def clean(self):
        uninstall_docker_command = "{} ssh {} 'sudo apt-get purge -y docker-ce'".format(self.docker_machine_bin, self.name)
        print(pipeline(uninstall_docker_command))
