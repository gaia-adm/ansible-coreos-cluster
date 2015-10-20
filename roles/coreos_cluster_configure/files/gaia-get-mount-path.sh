#!/bin/bash
# returns mount location of volume. Avoids the mount path being hardcoded in fleet unit files.

function echoerr() {
  echo "$@" 1>&2;
}

if [ -z "$1" ]; then
  echoerr "Missing volume name argument"
  exit 1
fi

if [[ "$1" = shared* ]] ; then
  echoerr "Shared volumes not yet supported"
  exit 1
else
  # not shared volume
  echo "/var/lib/rexray/volumes/$1"
fi
