import pytest

from floop.dependency.host.docker import Docker
from floop.dependency.host.host_dependency import InstallHostDependencyException

def test_docker_init():
    Docker()

def test_docker_install():
    Docker().install(sudo=True, verify=True)

def test_docker_install_no_sudo_fails():
    with pytest.raises(InstallHostDependencyException):
        Docker().install(sudo=False, verify=True)
