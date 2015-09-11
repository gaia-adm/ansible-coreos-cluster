#!/bin/sh
export EC2_INI_PATH=inventory/ec2.ini
ansible-playbook --extra-vars "env=$1" main.yaml
