import pytest

from floop.dependency.docker import Docker, InstallDockerException

def test_docker_init():
    Docker()

def test_docker_install():
    Docker().install(sudo=True, verify=True)

def test_docker_install_no_sudo_fails():
    with pytest.raises(InstallDockerException):
        Docker().install(sudo=False, verify=True)
