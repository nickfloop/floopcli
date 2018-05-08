import pytest

from os import remove
from os.path import isfile

from floop.util.syscall import syscall, SystemCallException
from floop.test.floop_test.fixture import fixture_valid_config_file

@pytest.fixture(scope='function')
def fixture_cli_base(request):
    test_config_file = fixture_valid_config_file(request)
    return ['floop', 'floop -c {}'.format(test_config_file)]

@pytest.fixture(scope='module')
def fixture_supported_cli_commands():
    return {
            #'config' : [],
            'init' : [],
            'push' : [],
            #'build' : [],
            #'run' : [],
            #'clean' : []
            }

def test_cli_unknown_command_fails(fixture_cli_base):
    for base in fixture_cli_base:
        with pytest.raises(SystemCallException):
            syscall('{} notactuallyacommand'.format(base), check=True)

def test_cli_commands_no_flags(fixture_cli_base, fixture_supported_cli_commands):
    for base in fixture_cli_base:
        for command in fixture_supported_cli_commands.keys():
            sys_string = '{} {}'.format(base, command)
            print(sys_string)
            syscall(sys_string, check=True)

def test_cli_config_overwrite():
    syscall('floop config --overwrite', check=True)
