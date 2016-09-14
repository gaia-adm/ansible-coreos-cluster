#!/bin/bash

for m in $(ssh -F keys/us-east-1/ssh_config_prod 10.10.3.55 fleetctl list-machines --fields ip -no-legend); do 
  ssh -F keys/us-east-1/ssh_config_prod $m "sudo bash -c \"echo GROUP=$1 > /etc/coreos/update.conf\""
  ssh -F keys/us-east-1/ssh_config_prod $m "cp /usr/share/coreos/release /tmp"
  ssh -F keys/us-east-1/ssh_config_prod $m "sudo bash -c \"mount -o bind /tmp/release /usr/share/coreos/release\""
  ssh -F keys/us-east-1/ssh_config_prod $m "sed \"s/COREOS_RELEASE_VERSION=.*/COREOS_RELEASE_VERSION=0.0.0/g\" /usr/share/coreos/release > /tmp/0-release"
  ssh -F keys/us-east-1/ssh_config_prod $m "mv /tmp/0-release /tmp/release"
  ssh -F keys/us-east-1/ssh_config_prod $m "sudo bash -c \"systemctl restart update-engine\""
  ssh -F keys/us-east-1/ssh_config_prod $m "update_engine_client -update"
done
