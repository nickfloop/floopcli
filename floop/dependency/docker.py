from floop.util.syscall import syscall, SystemCallException
from platform import system, dist
from os.path import isfile
from os import remove, listdir

class UnsupportedOperatingSystem(Exception):
    pass

class InstallDockerException(Exception):
    pass

class VerifyDockerInstalledException(Exception):
    pass

class Docker(object):
    def __init__(self):
        operating_system = system()
        if operating_system != 'Linux':
            raise UnsupportedOperatingSystem(operating_system)

    def install(self, sudo=False, verify=False):
        self.sudo = sudo
        self.__install_apt_packages()
        self.__add_apt_repo()
        self.__install_docker()
        if verify:
            self.__verify()

    def __install_apt_packages(self):
        apt_update = 'apt-get update'
        apt_install = 'apt-get install -y apt-transport-https ca-certificates curl gnupg2 lsb-release software-properties-common'
        commands = [apt_update, apt_install]
        for command in commands:
            if self.sudo:
                command = 'sudo {}'.format(command)
            print(command)
            try:
                syscall(command, check=True)
            except SystemCallException:
                raise InstallDockerException(command)

    def __add_apt_repo(self):
        flavor, version, distro = dist()
        flavor = flavor.lower()
        key_file = 'docker.key'
        download_key = 'curl -o {} -fsSL https://download.docker.com/linux/{}/gpg'.format(key_file, flavor)
        add_key = 'apt-key add {}'.format(key_file) 
        add_repo = 'add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/{} {} stable"'.format(flavor, distro)
        commands = [download_key, add_key, add_repo]
        try:
            for command in commands:
                if self.sudo:
                    command = 'sudo {}'.format(command)
                print(command)
                syscall(command, check=True)
        except SystemCallException:
            raise InstallDockerException(command)
        finally:
            if isfile(key_file):
                remove(key_file)

    def __install_docker(self):
        apt_update = 'apt-get update'
        apt_install = 'apt-get install -y docker-ce' 
        commands = [apt_update, apt_install]
        try:
            for command in commands:
                if self.sudo:
                    command = 'sudo {}'.format(command)
                print(command)
                syscall(command, check=True)
        except SystemCallException:
            raise InstallDockerException(command)

    def __verify(self):
        check_version = 'docker --version'
        try:
            syscall(check_version, check=True)
        except SystemCallException:
            raise VerifyDockerInstalledException(command)
