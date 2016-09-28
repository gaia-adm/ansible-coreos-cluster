#!/usr/bin/env bats

load helpers

@test "check 'keys' directory exists" {
  [ -d "$(pwd)/keys" ]
}

@test "check 'keys/$AWS_REGION' directory exists" {
  [ -d "$(pwd)/keys/$AWS_REGION" ]
}

@test "check bastion keypair" {
  _bastion_key_file="$(pwd)/keys/$AWS_REGION/bastion-key-${ENV}.pem"
  [ -f "$_bastion_key_file" ]
  run ec2fp "$_bastion_key_file"
  [ "$status" -eq 0 ]
  _fingerprint="$output"
  run bash -c "aws ec2 describe-key-pairs --key-name bastion-keypair-${ENV} | jq -r '.KeyPairs | .[].KeyFingerprint'"
  [ "$status" -eq 0 ]
  [ "$output" == "$_fingerprint" ]
}

@test "check coreos keypair" {
  _coreos_key_file="$(pwd)/keys/$AWS_REGION/coreos-key-${ENV}.pem"
  [ -f "$_coreos_key_file" ]
  run ec2fp "$_coreos_key_file"
  [ "$status" -eq 0 ]
  _fingerprint="$output"
  run bash -c "aws ec2 describe-key-pairs --key-name coreos-keypair-${ENV} | jq -r '.KeyPairs | .[].KeyFingerprint'"
  [ "$status" -eq 0 ]
  [ "$output" == "$_fingerprint" ]
}

@test "check docker registry keypair" {
  _registry_key_file="$(pwd)/keys/$AWS_REGION/docker-registry-key-${ENV}.pem"
  [ -f "$_registry_key_file" ]
  run ec2fp "$_registry_key_file"
  [ "$status" -eq 0 ]
  _fingerprint="$output"
  run bash -c "aws ec2 describe-key-pairs --key-name docker-registry-keypair-${ENV} | jq -r '.KeyPairs | .[].KeyFingerprint'"
  [ "$status" -eq 0 ]
  [ "$output" == "$_fingerprint" ]
}

@test "check etcd keypair" {
  _etcd_key_file="$(pwd)/keys/$AWS_REGION/etcd-key-${ENV}.pem"
  [ -f "$_etcd_key_file" ]
  run ec2fp "$_etcd_key_file"
  [ "$status" -eq 0 ]
  _fingerprint="$output"
  run bash -c "aws ec2 describe-key-pairs --key-name etcd-keypair-${ENV} | jq -r '.KeyPairs | .[].KeyFingerprint'"
  [ "$status" -eq 0 ]
  [ "$output" == "$_fingerprint" ]
}
