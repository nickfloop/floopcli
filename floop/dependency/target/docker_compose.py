#TODO: make sure you download Docker Compose for ARM!!!

from platform import uname, system

from floop.dependency.os import check_os
from floop.dependency.exception import InstallDependencyException
from floop.util.syscall import syscall, SystemCallException

class DockerCompose(object):
    def __init__(self):
        check_os()

    def install(self, sudo=False, verify=False):
        self.sudo = sudo
        self.__download_and_make_executable()
        if verify:
            self.__verify()
       
    def __download_and_make_executable(self):
        #self.os = system()
        #self.processor = uname()['processor']
        #download_bin = 'curl -L https://github.com/docker/compose/releases/download/1.21.0/docker-compose-{}-{} -o /usr/local/bin/docker-compose'.format(self.system.lower(), self.processor)
        #make_executable = 'chmod +x /usr/local/bin/docker-compose'
        download_pip = 'curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py'
        install_pip = 'python get-pip.py'
        install_docker_compose = 'pip install docker-compose'
        commands = [download_bin, make_executable]
        for command in commands:
            if self.sudo:
                command = 'sudo {}'.format(command)
            print(command)
            try:
                syscall(command, check=True, verbose=True)
            except SystemCallException:
                raise InstallDependencyException(command)

    def __verify(self):
        check_version = 'docker-compose --version'
        try:
            syscall(check_version, check=True)
        except SystemCallException:
            raise InstallDependencyException('docker-compose: {}'.format(check_version))
