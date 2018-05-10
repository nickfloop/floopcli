import pytest
import json
from copy import copy

from os import remove
from os.path import isfile
from itertools import combinations

from floop.util.syscall import syscall, SystemCallException
from floop.test.floop_test.fixture import fixture_valid_config_file

@pytest.fixture(scope='function')
def fixture_unknown_cli_commands():
    return [
            'notactuallyacommand',
            'not actuallyacommand',
            'not actually acommand',
            'not actually a command',
            'n o t a c t u a l l y a c o m m a n d'
            ]

@pytest.fixture(scope='function')
def fixture_cli_base(request):
    test_config_file = fixture_valid_config_file(request)
    return ['floop', 'floop -c {}'.format(test_config_file)]

@pytest.fixture(scope='function')
def fixture_cli_base_nonexistent_config_file():
    return 'floop -c definitelynotarealconfigfile.json' 

@pytest.fixture(scope='module')
def fixture_supported_cli_commands():
    return {
            #'config' : [],
            'create' : [],
            'ps' : [],
            'push' : [],
            'build' : [],
            'run' : [],
            'logs' : [],
            'test' : []
            #'clean' : []
            }

@pytest.fixture(scope='function')
def fixture_incompatible_cli_commands():
    return [
            'floop -c floop.json config'
            ]

@pytest.fixture(scope='function')
def fixture_malformed_floop_configs(request):
    test_config_file = fixture_valid_config_file(request)
    with open(test_config_file) as tcf:
        valid_config = json.load(tcf)
    config_files = ['malformed-config-{}.json'.format(key) for key
            in sorted(valid_config.keys())]
    def cleanup():
        for cf in config_files:
            if isfile(cf):
                remove(cf)
    cleanup()
    request.addfinalizer(cleanup)
    for idx, key in enumerate(sorted(valid_config.keys())):
        config = copy(valid_config)
        del config[key]
        print(config)
        config_file = config_files[idx]
        with open(config_file, 'w') as cf:
            json.dump(config, cf)
    return config_files


@pytest.fixture(scope='function')
def fixture_nonexistent_source_dir_config(request):
    test_config_file = fixture_valid_config_file(request)
    with open(test_config_file) as tcf:
        invalid_config = json.load(tcf)
    invalid_config['host_source_directory'] = 'definitely/not/a/real/directory/'
    config_file = 'config-nonexistent-source-dir.json'
    def cleanup():
        if isfile(config_file):
            remove(config_file)
    cleanup()
    request.addfinalizer(cleanup)
    with open(config_file, 'w') as cf:
        json.dump(invalid_config, cf)
    return config_file 

def test_cli_bases_fail(fixture_cli_base):
    for base in fixture_cli_base:
        with pytest.raises(SystemCallException):
            syscall(base, check=True)

def test_cli_commands_with_flags(fixture_cli_base, fixture_supported_cli_commands):
    for base in fixture_cli_base:
        for command, flags in fixture_supported_cli_commands.items():
            for i in range(1, len(flags)+1):
                for combo in combinations(flags, i):
                    combo = ' '.join(list(combo))
                    sys_string = '{} {} {}'.format(base, command, combo)
                    print(sys_string)
                    syscall(sys_string, check=True)


def test_cli_commands_nonexistent_source_dir_fails(fixture_nonexistent_source_dir_config, fixture_supported_cli_commands):
    for command in fixture_supported_cli_commands.keys():
        with pytest.raises(SystemCallException):
            syscall('floop -c {} {}'.format(
                fixture_nonexistent_source_dir_config, command), check=True)

def test_cli_commands_malformed_configs_fails(fixture_malformed_floop_configs, fixture_supported_cli_commands):
    for config in fixture_malformed_floop_configs:
        for command in fixture_supported_cli_commands.keys():
            with pytest.raises(SystemCallException):
                syscall('floop -c {} {}'.format(
                    config, command), check=True)

def test_cli_commands_nonexistent_config_fails(fixture_cli_base_nonexistent_config_file, fixture_supported_cli_commands):
    for command in fixture_supported_cli_commands.keys():
        with pytest.raises(SystemCallException):
            syscall('{} {}'.format(
                fixture_cli_base_nonexistent_config_file, command), check=True)

def test_incompatible_cli_commands_fail(fixture_incompatible_cli_commands):
    for command in fixture_incompatible_cli_commands:
        with pytest.raises(SystemCallException):
            syscall(command, check=True)

def test_cli_unknown_commands_fail(fixture_cli_base, fixture_unknown_cli_commands):
    for base in fixture_cli_base:
        for command in fixture_unknown_cli_commands:
            with pytest.raises(SystemCallException):
                syscall('{} {}'.format(base, command), check=True)

def test_cli_commands_no_flags(fixture_cli_base, fixture_supported_cli_commands):
    for base in fixture_cli_base:
        for command in fixture_supported_cli_commands.keys():
            sys_string = '{} {}'.format(base, command)
            print(sys_string)
            syscall(sys_string, check=True)

def test_cli_config_overwrite():
    syscall('floop config', check=True)
    syscall('floop config', check=True)
    syscall('floop config --overwrite', check=True)
