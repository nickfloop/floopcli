import os
import boto3

def get_client(service):
    return boto3.client(
        service_name = service,
        region_name = os.environ['AWS_DEFAULT_REGION'], 
        aws_access_key_id = os.environ['AWS_ACCESS_KEY'],
        aws_secret_access_key = os.environ['AWS_SECRET_KEY']
    )
def docker_machine_string(name):
        return '''docker-machine create \
--amazonec2-region={} \
--amazonec2-access-key={} \
--amazonec2-secret-key={} \
{}'''.format(
        os.environ['AWS_DEFAULT_REGION'],
        os.environ['AWS_ACCESS_KEY'],
        os.environ['AWS_SECRET_KEY'],
        name)

def lambda_handler(event, context):
    '''
    AWS Lambda function for floop-cli integration testing
    '''

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
sudo apt-get update && sudo apt-get install curl rsync &&

# install docker-machine
base=https://github.com/docker/machine/releases/download/v0.14.0 &&\
  curl -L $base/docker-machine-$(uname -s)-$(uname -m) >/tmp/docker-machine &&\
  sudo install /tmp/docker-machine /usr/local/bin/docker-machine

# start "target" ec2 instances as AWS Docker Machines
{}

{}

# no matter what happens, call cleanup
trap cleanup EXIT ERR INT TERM'''.format(
        'test0',
        'test1',
        docker_machine_string('test0'),
        docker_machine_string('test1')
    )

    print(init_script)

    #instance = ec2.run_instances(
    #    # use env default or default AMI for ap-southeast-1
    #    ImageId=os.environ.get('DEFAULT_AMI') or 'ami-2378f540',
    #    # use env default or smallest ec2 instance
    #    InstanceType=os.environ.get('DEFAULT_INSTANCE_TYPE') or 't2.nano',
    #    MinCount=1,
    #    MaxCount=1,
    #    InstanceInitiatedShutdownBehavior='terminate',
    #    UserData=init_script
    #)

    #instance_id = instance['Instances'][0]['InstanceId']
    #print(instance_id)
    #return instance_id

if __name__ == '__main__':
    lambda_handler(None, None)
