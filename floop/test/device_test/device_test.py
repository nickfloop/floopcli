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
from floop.test.floop_test.fixture import *
#fixture_valid_device_config, \
#        fixture_valid_docker_machine


@pytest.fixture(scope='function')
def fixture_valid_device():
    valid_config = fixture_valid_device_config()
    device = Device(docker_machine_bin=fixture_docker_machine_bin(), **valid_config)
    create(device, check=True)
    return device


def test_device_init(fixture_docker_machine_bin, fixture_valid_device_config):
    device = Device(
            docker_machine_bin=fixture_docker_machine_bin,
            **fixture_valid_device_config)

def test_device_create_invalid_config_fails(fixture_docker_machine_bin,
        fixture_invalid_device_configs):
    for config in fixture_invalid_device_configs:
        device = Device(
                docker_machine_bin=fixture_docker_machine_bin,
                **config)
        with pytest.raises(DeviceCreateException):
            create(device)

def test_device_init_nonexistent_ssh_key_fails(fixture_docker_machine_bin,
        fixture_valid_device_config):
    config = fixture_valid_device_config
    config['ssh_key'] = '/definitely/not/a/valid/ssh/key'
    with pytest.raises(SSHKeyNotFound):
        Device(
            docker_machine_bin=fixture_docker_machine_bin,
            **fixture_valid_device_config)

def test_device_set_attributes_after_init_fails(fixture_docker_machine_bin,
        fixture_valid_device_config):
    device = Device(
            docker_machine_bin=fixture_docker_machine_bin,
            **fixture_valid_device_config)
    for key in fixture_valid_device_config.keys():
        with pytest.raises(CannotSetImmutableAttribute):
            setattr(device, key, fixture_valid_device_config[key])

def test_device_run_ssh_command_pwd(fixture_valid_device):
    fixture_valid_device.run_ssh_command(command='pwd', check=True)

def test_device_push(fixture_valid_device, fixture_valid_src_directory,
        fixture_valid_target_directory):
    push(fixture_valid_device,
        source_directory=fixture_valid_src_directory,
        target_directory=fixture_valid_target_directory
    )

def test_device_push_nonexistent_src_dir_fails(fixture_valid_device,
        fixture_valid_target_directory):
    with pytest.raises(DeviceSourceDirectoryNotFound):
        push(fixture_valid_device,
            source_directory='definitely/not/a/real/src/dir',
            target_directory=fixture_valid_target_directory
        )

def test_device_push_restricted_target_dir_fails(fixture_valid_device,
        fixture_valid_src_directory):
    with pytest.raises(DeviceCommunicationException):
        push(fixture_valid_device,
            source_directory=fixture_valid_src_directory,
            target_directory='/.test/'
        )

def test_device_build(fixture_valid_device, 
        fixture_buildfile, fixture_valid_target_directory):
    build(fixture_valid_device,
        source_directory=fixture_buildfile,
        target_directory=fixture_valid_target_directory
    )

def test_device_build_no_buildfile_fails(fixture_valid_device, 
        fixture_valid_src_directory, fixture_valid_target_directory):
    with pytest.raises(DeviceBuildFileNotFound):
        build(fixture_valid_device,
            source_directory=fixture_valid_src_directory,
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
