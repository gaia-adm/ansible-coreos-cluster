#!/usr/bin/env bats

@test "aws cli install" {
  run which aws
  [ "$status" -eq 0 ]
}

@test "check aws clonfiguration: access_key_id" {
  if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    run aws configure get aws_access_key_id
  else
    run true
  fi
  [ "$status" -eq 0 ]
}

@test "check aws clonfiguration: secret_access_key" {
  if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    run aws configure get aws_secret_access_key
  else
    run true
  fi
  [ "$status" -eq 0 ]
}

@test "check aws clonfiguration: region" {
  if [ -z "$AWS_DEFAULT_REGION" ]; then
    run aws configure get region
  else
    run true
  fi
  [ "$status" -eq 0 ]
}
