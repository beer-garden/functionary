#!/bin/bash

# This is pretty basic and always builds all of the templates.

push=$1
registry="${REGISTRY_HOST:-localhost}:${REGISTRY_PORT:-5000}"
dirs=`ls -1d */ | sed 's/\///'`

for dir in ${dirs[@]}; do
    pushd $dir > /dev/null
    docker build -t ${registry}/templates/${dir}:latest .
    popd > /dev/null

    if [ "${push}" = "-p" ]; then
        docker push ${registry}/templates/${dir}:latest
    fi
done
