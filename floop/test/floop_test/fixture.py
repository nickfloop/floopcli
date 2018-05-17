import pytest

import json

from copy import copy
from os import remove, environ, mkdir
from os.path import abspath, dirname, isfile, isdir

from shutil import rmtree, which

from floop.config import _FLOOP_CONFIG_DEFAULT_CONFIGURATION
from floop.util.syscall import syscall

FLOOP_TEST_CONFIG_FILE = './floop.json' 

FLOOP_TEST_CONFIG = _FLOOP_CONFIG_DEFAULT_CONFIGURATION

_TEST_DEVICE_NAME = 'test0'

_DEVICE_TEST_SRC_DIRECTORY = '{}/src/'.format(dirname(
    abspath(__file__))
    )

@pytest.fixture(scope='function')
def fixture_default_config_file(request):
    config_file = FLOOP_TEST_CONFIG_FILE
    config = FLOOP_TEST_CONFIG
    def cleanup():
        if isfile(config_file):
            remove(config_file)
    cleanup()
    with open(config_file, 'w') as cf:
        json.dump(config, cf)
    request.addfinalizer(cleanup)
    return config_file

# keep these fixtures separate to allow for fine-grained
# refactoring using different env variables

@pytest.fixture(autouse=True)
def fixture_valid_docker_machine():
    if environ.get('FLOOP_LOCAL_HARDWARE_TEST'):
        pass
    elif environ.get('FLOOP_CLOUD_TEST'):
        pass
    # default to local 1GB Virtualbox machine
    else: 
        create_local_machine = '''docker-machine create 
        --driver virtualbox 
        --virtualbox-memory 1024
        {}'''.format(_TEST_DEVICE_NAME)
        syscall(create_local_machine, check=False)

@pytest.fixture(scope='function')
def fixture_docker_machine_wrapper():
    def method():
        fixture_valid_docker_machine
    return method

@pytest.fixture(scope='function')
def fixture_valid_device_config():
    if environ.get('FLOOP_LOCAL_HARDWARE_TEST'):
        pass
    elif environ.get('FLOOP_CLOUD_TEST'):
        pass
    else: 
        return {'address' : '192.168.1.100',
                'name' : _TEST_DEVICE_NAME, 
                'ssh_key' :  '~/.ssh/id_rsa', 
                'user' : 'floop'}

@pytest.fixture(scope='function')
def fixture_valid_config_file(request):
    if environ.get('FLOOP_LOCAL_HARDWARE_TEST'):
        pass
    elif environ.get('FLOOP_CLOUD_TEST'):
        pass
    else: 
        src_dir = fixture_valid_src_directory(request)
        device_config = fixture_valid_device_config()
        config_file = fixture_default_config_file(request)
        with open(config_file, 'r') as cf:
            data = json.load(cf)
        data['devices'] = [device_config]
        data['host_source_directory'] = src_dir
        with open(config_file, 'w') as cf:
            json.dump(data, cf)
        return config_file

#
#

@pytest.fixture(scope='function')
def fixture_valid_src_directory(request):
    src_dir = _DEVICE_TEST_SRC_DIRECTORY 
    if isdir(src_dir):
        rmtree(src_dir)
    mkdir(src_dir)
    def cleanup():
        if isdir(src_dir):
            rmtree(src_dir)
    request.addfinalizer(cleanup)
    return src_dir

@pytest.fixture(scope='module')
def fixture_docker_machine_bin():
    return which('docker-machine') 

@pytest.fixture(scope='function')
def fixture_invalid_device_configs():
    config = fixture_valid_device_config()
    invalid_items = {'address' : '192.168.1.1222222',
            'user' : 'definitelyanunauthorizeduser'}
    configs = []
    for key, val in invalid_items.items():
        invalid_config = copy(config)
        invalid_config['name'] = 'thisshouldfail'
        invalid_config[key] = val
        configs.append(invalid_config)
    return configs 

@pytest.fixture(scope='function')
def fixture_valid_target_directory():
    return '/home/floop/floop'

@pytest.fixture(scope='function')
def fixture_buildfile(request):
    src_dir = fixture_valid_src_directory(request)
    buildfile = '{}/Dockerfile'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
RUN sh''' 
    with open(buildfile, 'w') as bf:
        bf.write(buildfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_failing_buildfile(request):
    src_dir = fixture_valid_src_directory(request)
    buildfile = '{}/Dockerfile'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
RUN apt-get update''' 
    with open(buildfile, 'w') as bf:
        bf.write(buildfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_failing_runfile(request):
    src_dir = fixture_valid_src_directory(request)
    buildfile = '{}/Dockerfile'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
CMD ["apt-get", "update"]''' 
    with open(buildfile, 'w') as bf:
        bf.write(buildfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_testfile(request):
    src_dir = fixture_valid_src_directory(request)
    testfile = '{}/Dockerfile.test'.format(_DEVICE_TEST_SRC_DIRECTORY)
    testfile_contents = '''FROM busybox:latest
run sh''' 
    with open(testfile, 'w') as tf:
        tf.write(testfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_failing_testfile(request):
    src_dir = fixture_valid_src_directory(request)
    buildfile = '{}/Dockerfile.test'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
CMD ["apt-get", "update"]''' 
    with open(buildfile, 'w') as tf:
        tf.write(buildfile_contents)
    return src_dir


