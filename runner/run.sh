#!/bin/bash

# Run script for app in Docker container

##########################
# User defined functions #
##########################

start() {
    python runner.py
}

######################
# Script starts here #
######################

####
# Expected run modes (passed in via docker run cmd)
# start             - Start application in Production mode
####

source $HOME/venv/bin/activate

mode=$1
case $mode in
    start|*)
    start;;
esac
