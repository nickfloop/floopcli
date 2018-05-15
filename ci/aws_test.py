import os
import boto3

def get_client(service):
    return boto3.client(
        service_name = service,
        region_name = 'ap-southeast-1', 
        aws_access_key_id = os.environ['AWS_ACCESS_KEY'],
        aws_secret_access_key = os.environ['AWS_SECRET_KEY']
    )

ec2 = get_client('ec2')

init_script = '''#!/bin/bash

sudo apt-get update && sudo apt-get install curl rsync python3-pip

base=https://github.com/docker/machine/releases/download/v0.14.0 &&\
  curl -L $base/docker-machine-$(uname -s)-$(uname -m) >/tmp/docker-machine &&\
  sudo install /tmp/docker-machine /usr/local/bin/docker-machine

shutdown -H 10'''

instance = ec2.run_instances(
    ImageId='ami-2378f540',
    InstanceType='t2.nano',
    MinCount=1,
    MaxCount=1,
    InstanceInitiatedShutdownBehavior='terminate',
    UserData=init_script
)

print(instance['Instances'][0]['InstanceId'])
