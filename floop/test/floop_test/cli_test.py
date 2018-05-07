import pytest

from floop.util.syscall import syscall, SystemCallException

def test_floop_unknown_command_fails():
    with pytest.raises(SystemCallException):
        syscall('floop notactuallyacommand', check=True)

def test_floop_config():
    syscall('floop config', check=True)

def test_floop_config_overwrite():
    syscall('floop config --overwrite', check=True)

def test_floop_config_overwrite_then_init_fails():
    print(syscall('floop config --overwrite', check=True))
    with pytest.raises(SystemCallException):
        print(syscall('floop init', check=True))
