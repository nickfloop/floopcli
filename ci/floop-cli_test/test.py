import os
import boto3

'''
Note:
    AWS_DEFAULT_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY are protected by Lambda
    Add a trailing _ to define your own. Make sure these values are defined
    in the Lambda dashboard.
'''

def get_client(service):
    return boto3.client(
        service_name = service,
        region_name = os.environ['AWS_DEFAULT_REGION_'], 
        aws_access_key_id = os.environ['AWS_ACCESS_KEY_'],
        aws_secret_access_key = os.environ['AWS_SECRET_KEY_']
    )

def docker_machine_string(name):
        return '''docker-machine create \
--driver amazonec2 \
--amazonec2-instance-type=t2.nano \
--amazonec2-region={} \
--amazonec2-access-key={} \
--amazonec2-secret-key={} \
{}'''.format(
        os.environ['AWS_DEFAULT_REGION_'],
        os.environ['AWS_ACCESS_KEY_'],
        os.environ['AWS_SECRET_KEY_'],
        name)

def lambda_handler(event, context):
    '''
    AWS Lambda handler for floop-cli integration testing
    '''
    if event['config']['secret'] != \
            os.environ['FLOOP_CLI_GITHUB_WEBHOOK_SECRET']:
        raise Exception('Incorrect Github webhook secret')

    ec2 = get_client('ec2')

    # this bash script runs as soon as the ec2 instance boots
    init_script = '''#!/bin/bash

# if any command fails, just clean up and exit
set -e

# force shutdown and terminate after a time limit, even if processes are running
shutdown -H 10

# clean up function to run at the end of testing
cleanup () {{
    docker-machine rm -f {}
    docker-machine rm -f {}
    shutdown -H now
}}

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

# local install floop-cli
cd floop-cli && sudo pip3 install -e .

# check static typing
mypy --ignore-missing-imports --disallow-untyped-defs floop/

# install docker-machine
base=https://github.com/docker/machine/releases/download/v0.14.0 &&\
  curl -L $base/docker-machine-$(uname -s)-$(uname -m) >/tmp/docker-machine &&\
  sudo install /tmp/docker-machine /usr/local/bin/docker-machine

# start "target" ec2 instances as AWS Docker Machines
{} &\
{} &\
wait

# run pytest on floop-cli, set cloud test env variable to true
#FLOOP_CLOUD_TEST=true pytest --cov-report term-missing --cov=floop -v -s -x floop

# no matter what happens, call cleanup
trap cleanup EXIT ERR INT TERM'''.format(
        'core0',
        'core1',
        os.environ['SSH_KEY'],
        docker_machine_string('core0'),
        docker_machine_string('core1')
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
    return instance_id

#if __name__ == '__main__':
#    lambda_handler(None, None)
