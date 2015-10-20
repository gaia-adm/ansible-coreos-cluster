#!/bin/sh
export EC2_INI_PATH=inventory/ec2.ini
# we use sleep due to usage of auto scale groups, to give extra time
# for ssh to be available. Ansible wait_for cannot be used due to private IPs.
ansible-playbook --extra-vars "env=$1" main_setup.yaml \
&& echo "Waiting for 60 seconds to make sure all machines are ready" \
&& sleep 60 \
&& ansible-playbook --extra-vars "env=$1" ssh_config_amazon.yaml \
&& ansible-playbook --extra-vars "env=$1" main_config.yaml
