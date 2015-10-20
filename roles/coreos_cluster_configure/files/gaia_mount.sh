#!/bin/bash

function echoerr() {
  echo "$@" 1>&2;
}

if [ -z "$1" ]; then
  echoerr "Missing volume name argument"
  exit 1
fi

function mount_nonshared_volume() {
  instance_id=$(rexray adapter instances | yaml2json | jq --raw-output '.[0].instanceid')

  for i in {1..4}
  do
    volume_info=$(rexray volume get --volumename=$1 | yaml2json)
    volume_count=$(echo $volume_info | jq '. | length')
    echoerr "Found $volume_count volume(s) with name $1"

    # check how many instances of volume with given name were found
    if [ $volume_count -eq 0 ]; then
      echoerr "Volume $1 not found, it must be created before gaia-mount is invoked"
      exit 1
    elif [ $volume_count -eq 1 ]; then
      # there is only 1 instance of the volume, check if its mounted somewhere else
      volume_instance_id=$(echo $volume_info | jq --raw-output '.[0].attachments[0].instanceid')
      volume_id=$(echo $volume_info | jq --raw-output '.[0].volumeid')

      if [ -z "$volume_instance_id" -o "$volume_instance_id" = "null" ]; then
        # volume is not mounted. It can exists in the same AZ or in different AZ than this machine
        error_file=$(mktemp)
        mount_out=$(rexray volume mount --volumeid=$volume_id 2>$error_file)
        mount_res=$?
        mount_err=$(< $error_file)
        rm $error_file
        # rexray logs on stderr, we joined it to stdout to be able to parse error
        echoerr $mount_err

        if [ $mount_res -eq 0 ]; then
          echoerr "Volume $1 has been mounted successfully"
          echo $mount_out
          exit 0
        else
          is_zone_mismatch=$(echo $mount_err | grep -c -e "InvalidVolume.ZoneMismatch")
          if [ "$is_zone_mismatch" -eq 1 ]; then
            # zone mismatch - volume cannot be mounted in this zone
            echoerr "Zone mismatch, migrating volume $1 to current availability zone"
            volume_type=$(echo $volume_info | jq --raw-output '.[0].volumetype')
            volume_iops=$(echo $volume_info | jq --raw-output '.[0].iops')

            # create copy of original volume in our AZ
            if [ "$volume_type" = "io1" ]; then
              create_out=$(rexray volume create --volumeid=$volume_id --volumename=$1 --volumetype=$volume_type --iops=$volume_iops | yaml2json)
              create_res=$?
            else
              create_out=$(rexray volume create --volumeid=$volume_id --volumename=$1 --volumetype=$volume_type | yaml2json)
              create_res=$?
            fi
            if [ "$create_res" -eq 0 ]; then
              new_volume_id=$(echo $create_out | jq --raw-output '.volumeid' )
              new_volume_az=$(echo $create_out | jq --raw-output '.availabilityzone' )
              echoerr "Created copy of volume $1 in availability zone $new_volume_az. Volume id $new_volume_id"
              # validate there are now two volumes with the same name, just in case rexray returns us 0 and fails to create copy...
              volume_count2=$(rexray volume get --volumename=$1 | yaml2json | jq '. | length')
              if [ "$volume_count2" -eq 2 ]; then
                echoerr "Deleting volume $1 in original availability zone"
                delete_out=$(rexray volume remove --volumeid=$volume_id)
                delete_res=$?
                if [ "$delete_res" -eq 0 ]; then
                  echoerr "Volume $1 was deleted in original availability zone and will be mounted in current availability zone"
                  mount_out=$(rexray volume mount --volumeid=$new_volume_id)
                  mount_res=$?
                  if [ "$mount_res" -eq 0 ] ; then
                    echoerr "Volume $1 has been mounted successfully"
                    echo $mount_out
                    exit 0
                  else
                    echoerr "Failed to mount volume $1 due to error. Rexray returned code $mount_res"
                    exit 1
                  fi
                else
                  echoerr "Failed to delete volume $1 in original availability zone"
                  exit 1
                fi
              else
                echoerr "Expected 2 volumes to exist with name $1, but found $volume_count2"
                exit 1
              fi
            else
              echoerr "Failed to create copy of volume $1 in current availability zone. Rexray returned code $create_res"
              exit 1
            fi
          else
            # unknown error
            echoerr "Failed to mount volume $1 due to error. Rexray returned code $mount_res"
            exit 1
          fi
        fi

      elif [ "$instance_id" = "$volume_instance_id" ]; then
        # volume is already mounted on this instance, nothing to do
        echoerr "Volume $1 is already mounted on this instance"
        exit 0
      else
        # volume is mounted on another instance
        echoerr "Volume $1 is already mounted on another instance $volume_instance_id. Unable to mount."
        echoerr "Waiting for 10s before trying again"
        sleep 10
      fi
    elif [ $volume_count -ge 2 ]; then
      echoerr "Volume $1 exists $volume_count times. To avoid data loss it will not be mounted. Please resolve this situation manually."
      exit 1
    fi
  done
  echoerr "Unable to mount volume $1 after $i tries"
}

if [[ "$1" = shared* ]] ; then
  echoerr "Shared volumes not yet supported"
  exit 1
else
  mount_nonshared_volume $1
fi
