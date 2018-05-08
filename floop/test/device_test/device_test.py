import pytest
from floop.device.device import Device, CannotSetImmutableAttributeException, CannotFindSSHKeyException
from floop.util.syscall import syscall

import os
import os.path
import json
from shutil import rmtree

_DEVICE_TEST_SRC_DIRECTORY = '{}/src/'.format(os.path.dirname(
    os.path.abspath(__file__))
    )

_DEVICE_TEST_SRC_FIXTURE_JSON = '{}/fixture.json'.format(
        _DEVICE_TEST_SRC_DIRECTORY) 

_DEVICE_TEST_SSH_KEY_DIRECTORY = '{}/key/'.format(os.path.dirname(
    os.path.abspath(__file__))
    )

_DEVICE_TEST_SSH_PRIVATE_KEY_FILE = '{}/ssh.key'.format(
        _DEVICE_TEST_SSH_KEY_DIRECTORY)

@pytest.fixture(scope='module')
def fixture_docker_machine_bin():
    return '/usr/local/bin/docker-machine'

@pytest.fixture(scope='module')
def valid_ssh_private_key(request):
    # this is a test key, don't worry
    # this key matches the test server at 
    # https://github.com/ForwardLoopLLC/floop-cli-dockerfiles/tree/master/floop-debian-jessie-ssh-sudo
    key = '''-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAtU6m/QlovcOI2Mt17BVERT8pfb5XzBI0qWQyORqO157z7uAS
itBbwhbmvFHfArLQj0okCRtZIo0imGZ0D5s24HcLtXWgfAPi50DodfG4VBj9hg/I
lMPmoOksB1bSpAf/fDQQE8OjvY/3a38ItQwoAi9r777uEdyafTeoYZbgX40qtMcC
FG5mX25MgfnS8cSmcL1Td0LVPtXc2qzAwzbxywtB0D8MA4AhsT5IQe2kYw5aJOoU
6Io0iRISDPvewMxFqSn6H06KfZaEomU81R4bgF0SM0NjO54E5wyLfdmlzGKnMmgP
8C41/j41HG5u3qJQU9SgD2os7S7PLqGpULsaXwIDAQABAoIBAFTEljx+FrOKZUP/
NH4Rn17E3jBFOyVVabu89eJO8XQMhD4uE11Fd3EyZeSsXpkTY4FrB5geajlGRWN9
m0vkpO6jmhzYBxWUd5TpewYR4r2nBXmVjZFIWl7nRceUp107xA6dBNtIwBiT4/kl
ZrvHGDmVVGC+Iu7E9pIO4LHn6bWiMEHuv8U/dTbn9BCqPt8CCaB3bOH2ZnnIWEXa
T+lWjJheydLbt7ZK99+mT3zymKipC6UN+KAnWtMM4X3P//tQx93UOIArOTBvS6qC
cMLUeSf9lNhN5QQrjLQTK9tkDMUfkiXUQ6GCsel3tV3es1JS43Iy9mvzaOCzSJeF
GJcVi/kCgYEA3p0JsscMqlig8L/zWE3HIt/ur+na62TY3UWknjoZkdBa3i03o+Jd
Fen1p54u4pQ87NyWNiun3KPa7CJyY44EjzgleDu20fTXmQJRwB1rnGizziQJWwv9
Nr4B8ZLD+A7glCHTc4KPE558DyvZI5v9l+FKMqjctEa0mnG/wJYrUW0CgYEA0H+3
FF4OW54F4yrq3smlbp/P31pY5W4ndQQN19z33MJXRmxInIF2V5fgfexW5s8pwGDz
1YefUjgUuubfnwNI86s5kw4QAI449VoYY6JXIvoHYl8oz11IUgtVLUroKQfnqJAD
W9KA2lZjME/HBTAxugi7XVwtZpHOYwAGPkfVB3sCgYAVsfJHBRUb6OVOcTaTDYlx
wacuZ7kZJcvozKe9b+YcCtVAP+HjS+VMhG+XdVgWZuIFJ35QKzMB0so8JyNExot1
NcCZFiC8F4OHeu1irrtVE/MqDOMIh4OW+S+RTn9gxnpmlWFZKYkuHUzz4Y8Y5FPz
oFYt170iqJ1jS+CnMTtphQKBgC+c2rwl9nVpksKbrGMP/V1T1W6V/TL3gr8wG9Et
vtSE9NU6KSLEVbgPEM7wx6+Ro2ExQr2CaRmngORlkK+JWoF6mn1AetsFn3A4ENW/
3tI38rO+M12XWcqSl/Lt5jJogbh2mq2/VnmFvMTtku9WYCSxlcfuItgHd/AXs1VJ
phY9AoGANZe99UxFEBFOb5274FLJWUxtB9ivgagkJMVzNI78NmL7FvkGNKCnEMkZ
h17zh7vulTa4ptBTARDUmd7ei+YarcLpyDvF45Qw3z/yS235MnMKy7w/ce+U9FuT
VGKOugFar0gIf3RyOAG3K0LoKBJR1rkqoE7I07BaQlXoDiMKbVQ=
-----END RSA PRIVATE KEY-----'''
    key_dir = _DEVICE_TEST_SSH_KEY_DIRECTORY 
    if os.path.isdir(key_dir):
        rmtree(key_dir)
    os.mkdir(key_dir)
    key_file = _DEVICE_TEST_SSH_PRIVATE_KEY_FILE 
    with open(key_file, 'w') as kf:
        kf.write(key)
    def cleanup():
        if isdir(key_dir):
            rmtree(key_dir)
    request.addfinalizer(cleanup)
    return key_file

@pytest.fixture(scope='function')
def fixture_valid_device_config():
    ssh_key = '~/.ssh/id_rsa'
    if os.path.isfile(_DEVICE_TEST_SSH_PRIVATE_KEY_FILE):
        ssh_key = _DEVICE_TEST_SSH_PRIVATE_KEY_FILE
    if os.environ.get('DEVICE0_PORT_22_TCP'):
        return {'address' : os.environ['DEVICE0_PORT_22_TCP_ADDR'],
                'name' : 'test0',
                'ssh_key' :  ssh_key,
                'user' : 'floop'
                }
    return {'address' : '192.168.1.122',
            'name' : 'op0',
            'ssh_key' :  ssh_key, 
            'user' : 'floop'}

@pytest.fixture(scope='module')
def fixture_valid_device(request):
    valid_config = fixture_valid_device_config()
    device = Device(docker_machine_bin=fixture_docker_machine_bin(), **valid_config)
    device.create()
    def cleanup():
        # remove when done testing non-create/destroy methods
        pass
        #cleanup_command = '{} rm -f {}'.format(
        #    device.docker_machine_bin,
        #    device.name
        #    )
        #print(cleanup_command)
        #out, err = syscall(cleanup_command)
    request.addfinalizer(cleanup) 
    return device

@pytest.fixture(scope='function')
def fixture_rsync_src_directory(request):
    src_dir = _DEVICE_TEST_SRC_DIRECTORY 
    if os.path.isdir(src_dir):
        rmtree(src_dir)
    os.mkdir(src_dir)
    fixture_file_contents = {'key':'value'}
    fixture_file = _DEVICE_TEST_SRC_FIXTURE_JSON 
    with open(fixture_file, 'w') as ff:
        json.dump(fixture_file_contents, ff)
    def cleanup():
        rmtree(src_dir)
    request.addfinalizer(cleanup)
    return src_dir

def test_device_init(fixture_docker_machine_bin, fixture_valid_device_config):
    device = Device(docker_machine_bin=fixture_docker_machine_bin,**fixture_valid_device_config)

def test_device_init_nonexistent_ssh_key_fails(fixture_docker_machine_bin, fixture_valid_device_config):
    config = fixture_valid_device_config
    config['ssh_key'] = '/definitely/not/a/valid/ssh/key'
    with pytest.raises(CannotFindSSHKeyException):
        Device(docker_machine_bin=fixture_docker_machine_bin,**fixture_valid_device_config)

def test_device_set_attributes_after_init_fails(fixture_docker_machine_bin, fixture_valid_device_config):
    device = Device(docker_machine_bin=fixture_docker_machine_bin,**fixture_valid_device_config)
    for key in fixture_valid_device_config.keys():
        with pytest.raises(CannotSetImmutableAttributeException):
            setattr(device, key, fixture_valid_device_config[key])

def test_device_run_ssh_command_pwd(fixture_valid_device):
    fixture_valid_device.run_ssh_command(command='pwd', check=True)

def test_device_rsync(fixture_valid_device, fixture_rsync_src_directory):
    fixture_valid_device.rsync(
        source_directory=fixture_rsync_src_directory,
        target_directory='/home/floop/.floop'
    )
    #rmtree(fixture_rsync_src_directory)
    fixture_valid_device.rsync(
        source_directory=fixture_rsync_src_directory,
        target_directory='/home/floop/.floop'
    )
    fixture_valid_device.run_ssh_command(command='ls')

#def test_device_clean(fixture_valid_device):
#    fixture_valid_device.clean()
