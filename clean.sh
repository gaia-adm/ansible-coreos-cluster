#!/bin/sh
export EC2_INI_PATH=inventory/ec2.ini

if [ $# -ne 2 ]; then
   echo 'Too few attributes: environment type and dns name must be provided'
   exit 1
fi

ansible-playbook --extra-vars "env=$1 dns=$2" clean.yaml
