import os
import boto3
import json
import hmac
import hashlib

from base64 import b64decode
from random import choice
from string import ascii_uppercase
from time import time

'''
Note:
    AWS_DEFAULT_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY are protected by Lambda
    Add a trailing _ to define your own. Make sure these values are defined
    in the Lambda dashboard..
'''

def decrypt(key):
    return boto3.client('kms').decrypt(CiphertextBlob=b64decode(os.environ[key]))['Plaintext'].decode('utf-8')

def validate_secret(event):
    sha, sig = event['headers']['X-Hub-Signature'].split('=')
    if sha != 'sha1':
        return False
    digest = hmac.new(
        bytes(os.environ['FLOOP_CLI_GITHUB_WEBHOOK_SECRET'], 'utf-8'),
        msg=bytes(event['body'], 'utf-8'),
        digestmod=hashlib.sha1).hexdigest()
    valid = hmac.compare_digest(digest.encode('utf-8'), sig.encode('utf-8'))
    return valid

def get_client(service):
    return boto3.client(
        service_name = service,
        region_name = decrypt('AWS_DEFAULT_REGION_'), 
        aws_access_key_id = decrypt('AWS_ACCESS_KEY_'),
        aws_secret_access_key = decrypt('AWS_SECRET_KEY_')
    )

def docker_machine_name():
    return ''.join(choice(ascii_uppercase) for i in range(16)) + str(int(time()*10000))

def docker_machine_string(name):
    return '''docker-machine create \
--driver amazonec2 \
--amazonec2-instance-type=t2.nano \
--amazonec2-region={} \
--amazonec2-access-key={} \
--amazonec2-secret-key={} \
{}'''.format(
        decrypt('AWS_DEFAULT_REGION_'),
        decrypt('AWS_ACCESS_KEY_'),
        decrypt('AWS_SECRET_KEY_'),
        name)

def lambda_handler(event, context):
    '''
    AWS Lambda handler for floop-cli integration testing
    '''
    if not validate_secret(event):
        return {
            'statusCode': 400,
            'body': json.dumps({'input': event, 'error' : 'Invalid Github secret'})
        }
    try:
        commit = json.loads(event['body'])['after']
    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({'input': event, 'error' : 'No commit ID'})
        }
    ec2 = get_client('ec2')

    cores = [docker_machine_name(), docker_machine_name()]

    # this bash script runs as soon as the ec2 instance boots
    init_script = '''#!/bin/bash

# if any command fails, just clean up and exit
set -e

# force shutdown and terminate after a time limit, even if processes are running
shutdown -H 10

# try to get ec2 to give any relevant information
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# clean up function to run at the end of testing
cleanup () {{
    docker-machine rm -f {}
    docker-machine rm -f {}
    shutdown -H now
}}

# no matter what happens, call cleanup
trap cleanup EXIT ERR INT TERM SIGINT SIGTERM

# install system dependencies
sudo apt-get update && sudo apt-get install -y curl git rsync python3-pip

mkdir -p ~/.ssh/
# the SSH_KEY env variable must contain slash-n newline characters
echo -e "{}" > ~/.ssh/id_rsa && chmod 700 ~/.ssh/id_rsa
cat ~/.ssh/id_rsa
ssh-keyscan github.com >> ~/.ssh/known_hosts
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_rsa' \
        git clone git@github.com:nickfloop/floop-cli-private.git \
        floop-cli

# checkout the commit that was just pushed
cd floop-cli && git checkout {}

# local install floop-cli
sudo pip3 install -e .

# check static typing
mypy --ignore-missing-imports --disallow-untyped-defs floop/

# install docker-machine
base=https://github.com/docker/machine/releases/download/v0.14.0 &&\
  curl -L $base/docker-machine-$(uname -s)-$(uname -m) >/tmp/docker-machine &&\
  sudo install /tmp/docker-machine /usr/local/bin/docker-machine

# start "target" ec2 instances as AWS Docker Machines, add ubuntu to docker group
{} && docker-machine ssh {} sudo usermod -aG docker ubuntu & \
{} && docker-machine ssh {} sudo usermod -aG docker ubuntu & \
wait

# run pytest on floop-cli, set cloud test env variable to true
FLOOP_CLOUD_TEST=true FLOOP_CLOUD_CORES={}:{} pytest --cov-report term-missing --cov=floop -v -s -x floop'''.format(
        cores[0],
        cores[1],
        decrypt('SSH_KEY'),
        commit,
        docker_machine_string(cores[0]),
        docker_machine_string(cores[1]),
        cores[0],
        cores[1],
        cores[0],
        cores[1]
    )

    print(init_script)

    instance = ec2.run_instances(
        # use env default or default AMI for ap-southeast-1
        ImageId=os.environ.get('DEFAULT_AMI') or 'ami-2378f540',
        # use env default or smallest ec2 instance
        InstanceType=os.environ.get('DEFAULT_INSTANCE_TYPE') or 't2.nano',
        MinCount=1,
        MaxCount=1,
        InstanceInitiatedShutdownBehavior='terminate',
        UserData=init_script
    )

    instance_id = instance['Instances'][0]['InstanceId']
    print(instance_id)
    return {
            'statusCode': 200,
            'body': json.dumps({'instance_id' : instance_id})
        }
