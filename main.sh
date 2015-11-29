#!/bin/sh
export EC2_INI_PATH=inventory/ec2.ini

# read input parameters
vflag=""
while [ $# -gt 0 ]
do
  case "$1" in
    -v) vflag="-vvvv";;
    -d) dns="$2"; shift;;
    -e) env="$2"; shift;;
    -h)
        echo >&2 "usage: $0 -e environment -d dns -v"
        exit 1;;
     *) break;; # terminate while loop
  esac
  shift
done

# we use sleep due to usage of auto scale groups, to give extra time
# for ssh to be available. Ansible wait_for cannot be used due to private IPs.
ansible-playbook --extra-vars "environ=$env dns=$dns" main_setup.yaml $vflag \
&& echo "Waiting for 60 seconds to make sure all machines are ready" \
&& sleep 60 \
&& ansible-playbook --extra-vars "environ=$env" ssh_config_amazon.yaml $vflag \
&& ansible-playbook --extra-vars "envviron=$env" main_config.yaml $vflag
