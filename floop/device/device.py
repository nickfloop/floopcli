from subprocess import check_output
from util.pipeline import pipeline

class CannotSetImmutableAttributeException(Exception):
    pass

class Device(object):
    def __init__(self, address: str, name: str) -> None:
        self.docker_machine_bin = '/usr/local/bin/docker-machine'
        self.address = address
        self.name = name
    
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

    def run_ssh_command(self, command: str) -> None:
        print(pipeline('{} ssh {} {}'.format(
            self.docker_machine_bin, self.name, command)
        ))

    def rsync(self,
            source_directory: str,
            target_directory: str,
            recursive: bool,
            verbose: bool=False) -> str:
        return pipeline("rsync -avz -e '{} ssh' {} {}:'{}' --delete".format(
            self.docker_machine_bin, source_directory,
            self.name, target_directory
            )
        )[0].decode('utf-8')
