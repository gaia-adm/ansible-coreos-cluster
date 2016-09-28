#!/usr/bin/env bats

@test "check Bastion VPC existence" {
  run bash -c "aws ec2 describe-vpcs --filters Name=tag:Name,Values=bastion | jq -r -e '.Vpcs | .[0] | .VpcId'"
  [ "$status" -eq 0 ]
}
