import pytest
from floop.device.device import Device, CannotSetImmutableAttributeException
from floop.util.pipeline import pipeline

import os
import os.path
import json
from shutil import rmtree

@pytest.fixture
def fixture_valid_device_config():
    return {'address' : '192.168.1.122',
            'name' : 'test0',
            'ssh_key' : '~/.ssh/id_rsa',
            'user' : 'floop'}

@pytest.fixture(scope='module')
def fixture_valid_device(request):
    valid_config = fixture_valid_device_config()
    device = Device(**valid_config)
    device.create()
    def cleanup():
        cleanup_command = '{} rm -f {}'.format(
            device.docker_machine_bin,
            device.name
            )
        print(cleanup_command)
        out, err = pipeline(cleanup_command)
    request.addfinalizer(cleanup) 
    return device

@pytest.fixture(scope='function')
def fixture_rsync_src_directory(request):
    this_file_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = '{}/src/'.format(this_file_dir)
    if os.path.isdir(src_dir):
        rmtree(src_dir)
    os.mkdir(src_dir)
    fixture_file_contents = {'key':'value'}
    fixture_file = '{}/fixture.json'.format(src_dir)
    with open(fixture_file, 'w') as ff:
        json.dump(fixture_file_contents, ff)
    def cleanup():
        rmtree(src_dir)
    request.addfinalizer(cleanup)
    return src_dir

def test_device_init(fixture_valid_device_config):
    device = Device(**fixture_valid_device_config)

def test_device_set_attributes_after_init_fails(fixture_valid_device_config):
    device = Device(**fixture_valid_device_config)
    for key in fixture_valid_device_config.keys():
        with pytest.raises(CannotSetImmutableAttributeException):
            setattr(device, key, fixture_valid_device_config[key])

def test_device_run_ssh_command_pwd(fixture_valid_device):
    fixture_valid_device.run_ssh_command(command='pwd')

def test_device_rsync(fixture_valid_device, fixture_rsync_src_directory):
    fixture_valid_device.rsync(
        source_directory=fixture_rsync_src_directory,
        target_directory='/home/floop/.floop'
    )

def test_device_clean(fixture_valid_device):
    fixture_valid_device.clean()
