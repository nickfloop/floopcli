import pytest
from floop.device.device import create, build, run, push, ps, test, destroy, \
        Device, DeviceCreateException, CannotSetImmutableAttribute, \
        SSHKeyNotFound, \
        DeviceSourceDirectoryNotFound, \
        DeviceCommunicationException, \
        DeviceBuildFileNotFound, \
        DeviceBuildException, \
        DeviceRunException, \
        DeviceTestException, \
        DeviceTestFileNotFound

import os
import os.path
import json
from shutil import rmtree, which
from copy import copy
from floop.util.syscall import syscall

_DEVICE_TEST_SRC_DIRECTORY = '{}/src/'.format(os.path.dirname(
    os.path.abspath(__file__))
    )

_TEST_DEVICE_NAME = 'test0'

@pytest.fixture(autouse=True)
def local_docker_machine():
    if os.environ.get('FLOOP_LOCAL_TEST'):
        create_local_machine = '''docker-machine create 
        --driver virtualbox 
        --virtualbox-memory 1024
        {}'''.format(_TEST_DEVICE_NAME)
        syscall(create_local_machine, check=False)

@pytest.fixture(scope='module')
def fixture_docker_machine_bin():
    return which('docker-machine') 

@pytest.fixture(scope='function')
def fixture_valid_device_config():
    return {'address' : '192.168.1.100',
            'name' : _TEST_DEVICE_NAME, 
            'ssh_key' :  '~/.ssh/id_rsa', 
            'user' : 'floop'}

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
def fixture_valid_device():
    valid_config = fixture_valid_device_config()
    device = Device(docker_machine_bin=fixture_docker_machine_bin(), **valid_config)
    create(device, check=True)
    return device

@pytest.fixture(scope='function')
def fixture_valid_target_directory():
    return '/home/floop/floop'

@pytest.fixture(scope='function')
def fixture_push_src_directory(request):
    src_dir = _DEVICE_TEST_SRC_DIRECTORY 
    if os.path.isdir(src_dir):
        rmtree(src_dir)
    os.mkdir(src_dir)
    def cleanup():
        rmtree(src_dir)
    request.addfinalizer(cleanup)
    return src_dir

@pytest.fixture(scope='function')
def fixture_buildfile(request):
    src_dir = fixture_push_src_directory(request)
    buildfile = '{}/Dockerfile'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
RUN sh''' 
    with open(buildfile, 'w') as bf:
        bf.write(buildfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_failing_buildfile(request):
    src_dir = fixture_push_src_directory(request)
    buildfile = '{}/Dockerfile'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
RUN apt-get update''' 
    with open(buildfile, 'w') as bf:
        bf.write(buildfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_failing_runfile(request):
    src_dir = fixture_push_src_directory(request)
    buildfile = '{}/Dockerfile'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
CMD ["apt-get", "update"]''' 
    with open(buildfile, 'w') as bf:
        bf.write(buildfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_testfile(request):
    src_dir = fixture_push_src_directory(request)
    testfile = '{}/Dockerfile.test'.format(_DEVICE_TEST_SRC_DIRECTORY)
    testfile_contents = '''FROM busybox:latest
run sh''' 
    with open(testfile, 'w') as tf:
        tf.write(testfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_failing_testfile(request):
    src_dir = fixture_push_src_directory(request)
    buildfile = '{}/Dockerfile.test'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
CMD ["apt-get", "update"]''' 
    with open(buildfile, 'w') as tf:
        tf.write(buildfile_contents)
    return src_dir

def test_device_init(fixture_docker_machine_bin, fixture_valid_device_config):
    device = Device(docker_machine_bin=fixture_docker_machine_bin,**fixture_valid_device_config)

def test_device_create_invalid_config_fails(fixture_docker_machine_bin,
        fixture_invalid_device_configs):
    for config in fixture_invalid_device_configs:
        device = Device(
                docker_machine_bin=fixture_docker_machine_bin,
                **config)
        with pytest.raises(DeviceCreateException):
            create(device)

def test_device_init_nonexistent_ssh_key_fails(fixture_docker_machine_bin, fixture_valid_device_config):
    config = fixture_valid_device_config
    config['ssh_key'] = '/definitely/not/a/valid/ssh/key'
    with pytest.raises(SSHKeyNotFound):
        Device(docker_machine_bin=fixture_docker_machine_bin,**fixture_valid_device_config)

def test_device_set_attributes_after_init_fails(fixture_docker_machine_bin, fixture_valid_device_config):
    device = Device(docker_machine_bin=fixture_docker_machine_bin,**fixture_valid_device_config)
    for key in fixture_valid_device_config.keys():
        with pytest.raises(CannotSetImmutableAttribute):
            setattr(device, key, fixture_valid_device_config[key])

def test_device_run_ssh_command_pwd(fixture_valid_device):
    fixture_valid_device.run_ssh_command(command='pwd', check=True)

def test_device_push(fixture_valid_device, fixture_push_src_directory, fixture_valid_target_directory):
    push(fixture_valid_device,
        source_directory=fixture_push_src_directory,
        target_directory=fixture_valid_target_directory
    )

def test_device_push_nonexistent_src_dir_fails(fixture_valid_device, fixture_valid_target_directory):
    with pytest.raises(DeviceSourceDirectoryNotFound):
        push(fixture_valid_device,
            source_directory='definitely/not/a/real/src/dir',
            target_directory=fixture_valid_target_directory
        )

def test_device_push_restricted_target_dir_fails(fixture_valid_device,
        fixture_push_src_directory):
    with pytest.raises(DeviceCommunicationException):
        push(fixture_valid_device,
            source_directory=fixture_push_src_directory,
            target_directory='/.test/'
        )

def test_device_build(fixture_valid_device, 
        fixture_buildfile, fixture_valid_target_directory):
    build(fixture_valid_device,
        source_directory=fixture_buildfile,
        target_directory=fixture_valid_target_directory
    )

def test_device_build_no_buildfile_fails(fixture_valid_device, 
        fixture_push_src_directory, fixture_valid_target_directory):
    with pytest.raises(DeviceBuildFileNotFound):
        build(fixture_valid_device,
            source_directory=fixture_push_src_directory,
            target_directory=fixture_valid_target_directory
        )

def test_device_build_docker_build_fail_fails(fixture_valid_device, 
        fixture_failing_buildfile, fixture_valid_target_directory):
    with pytest.raises(DeviceBuildException):
        build(fixture_valid_device,
            source_directory=fixture_failing_buildfile,
            target_directory=fixture_valid_target_directory
        )

def test_device_run(fixture_valid_device, 
        fixture_buildfile, fixture_valid_target_directory):
    run(fixture_valid_device,
        source_directory=fixture_buildfile,
        target_directory=fixture_valid_target_directory
    )

def test_device_run_docker_run_fail_fails(fixture_valid_device, 
        fixture_failing_runfile, fixture_valid_target_directory):
    with pytest.raises(DeviceRunException):
        run(fixture_valid_device,
            source_directory=fixture_failing_runfile,
            target_directory=fixture_valid_target_directory
        )

def test_device_ps(fixture_valid_device):
    ps(fixture_valid_device)

def test_device_test(fixture_valid_device, 
        fixture_testfile, fixture_valid_target_directory):
    test(fixture_valid_device,
        source_directory=fixture_testfile,
        target_directory=fixture_valid_target_directory
    )

def test_device_test_nonexistent_testfile_fails(fixture_valid_device, 
        fixture_buildfile, fixture_valid_target_directory):
    with pytest.raises(DeviceTestFileNotFound):
        test(fixture_valid_device,
            source_directory=fixture_buildfile,
            target_directory=fixture_valid_target_directory
        )

def test_device_test_docker_test_fail_fails(fixture_valid_device, 
        fixture_failing_testfile, fixture_valid_target_directory):
    with pytest.raises(DeviceTestException):
        test(fixture_valid_device,
            source_directory=fixture_failing_testfile,
            target_directory=fixture_valid_target_directory
        )

def test_device_destroy(fixture_valid_device, fixture_valid_target_directory):
    destroy(fixture_valid_device,
        target_directory=fixture_valid_target_directory)

def test_device_destroy(fixture_valid_device, fixture_valid_target_directory):
    destroy(fixture_valid_device,
        target_directory=fixture_valid_target_directory)
