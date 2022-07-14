#!/bin/bash

SCRIPT_DIR=`dirname -- $0`
BUILD_CONTEXT="${SCRIPT_DIR}/.."

docker build -f $SCRIPT_DIR/runner.Dockerfile -t package_runner:latest $BUILD_CONTEXT

if [ "$1" != "" ]; then
    docker tag package_runner:latest package_runner:$1
    echo "Successfully tagged package_runner:$1"
fi
