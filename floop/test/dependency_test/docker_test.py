import pytest

from floop.dependency.docker import Docker

def test_docker_init():
    Docker()

def test_docker_install():
    Docker().install()
