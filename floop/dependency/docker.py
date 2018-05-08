from floop.util.syscall import syscall
from platform import system, dist
from os.path import isfile
from os import remove

class UnsupportedOperatingSystem(Exception):
    pass

class Docker(object):
    def __init__(self):
        operating_system = system()
        if operating_system != 'Linux':
            raise UnsupportedOperatingSystem(operating_system)

    def install(self):
        self.__install_apt_packages()
        self.__add_apt_repo()
        self.__install_docker()

    def __install_apt_packages(self):
        apt_update = 'apt-get update'
        apt_install = 'apt-get install -y apt-transport-https ca-certificates curl gnupg2 lsb-release software-properties-common'
        commands = [apt_update, apt_install]
        for command in commands:
            print(command)
            syscall(command, check=True)

    def __add_apt_repo(self):
        flavor, version, distro = dist()
        flavor = flavor.lower()
        key_file = '/tmp/docker.key'
        download_key = 'curl -fsSL https://download.docker.com/linux/{}/gpg -o {}'.format(flavor, key_file)
        add_key = 'apt-key add {}'.format(key_file) 
        add_repo = 'add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/{} {} stable"'.format(flavor, distro)
        commands = [download_key, add_key, add_repo]
        for command in commands:
            print(command)
            syscall(command, check=True)
        if isfile(key_file):
            remove(key_file)

    def __install_docker(self):
        apt_update = 'apt-get update'
        apt_install = 'apt-get install -y docker-ce' 
        commands = [apt_update, apt_install]
        for command in commands:
            print(command)
            syscall(command, check=True)
