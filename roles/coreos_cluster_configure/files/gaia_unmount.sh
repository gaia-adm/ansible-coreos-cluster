#!/bin/bash

function echoerr() {
  echo "$@" 1>&2;
}

if [ -z "$1" ]; then
  echoerr "Missing volume name argument"
  exit 1
fi

function unmount_nonshared_volume() {
  instance_id=$(rexray adapter instances | yaml2json | jq --raw-output '.[0].instanceid')

  volume_info=$(rexray volume get --volumename=$1 | yaml2json)
  volume_count=$(echo $volume_info | jq '. | length')
  echoerr "Found $volume_count volume(s) with name $1"

  # check how many instances of volume with given name were found
  if [ $volume_count -eq 0 ]; then
    echoerr "Volume $1 not found"
    exit 1
  elif [ $volume_count -eq 1 ]; then
    # there is only 1 instance of the volume, check if its mounted somewhere else
    volume_instance_id=$(echo $volume_info | jq --raw-output '.[0].attachments[0].instanceid')
    volume_id=$(echo $volume_info | jq --raw-output '.[0].volumeid')

    if [ -z "$volume_instance_id" -o "$volume_instance_id" = "null" ]; then
      # volume is not mounted
      echoerr "Volume $1 is not mounted"
      exit 1
    elif [ "$instance_id" = "$volume_instance_id" ]; then
      # volume is mounted on this instance
      echoerr "Unmounting volume $1"
      unmount_out=$(rexray volume unmount --volumeid=$volume_id)
      unmount_res=$?
      if [ "$unmount_res" -eq 0 ]; then
        echoerr "Volume $1 has been unmounted successfully"
        exit 0
      else
        echoerr "Failed to unmount volume $1. Rexray returned code $unmount_res"
        exit 1
      fi
    else
      # volume is mounted on another instance
      echoerr "Volume $1 is mounted on another instance $volume_instance_id. Unable to unmount."
      exit 1
    fi

  elif [ $volume_count -ge 2 ]; then
    # do not unmount as then we would get 2 unmounted volumes with the same name, difficult to tell which one is the right one
    echoerr "Volume $1 exists $volume_count times. Unable to unmount."
    exit 1
  fi

}

if [[ "$1" = shared* ]] ; then
  echoerr "Shared volumes not yet supported"
  exit 1
else
  unmount_nonshared_volume $1
fi
