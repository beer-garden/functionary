#!/bin/bash

# Run script for app in Docker container

##########################
# User defined functions #
##########################

migrate() {
    python manage.py migrate
}

load_fixture() {
    python manage.py loaddata bootstrap
}

init() {
    migrate
    load_fixture
}

runserver() {
    python manage.py runserver 0.0.0.0:8000
}

run_listener() {
    python manage.py run_listener
}

run_worker() {
    python manage.py run_worker
}

run_build_worker() {
    python manage.py run_build_worker
}

start() {
    echo "Not yet implemented"
}

######################
# Script starts here #
######################

####
# Expected run modes (passed in via docker run cmd)
#
# init              - Migrate and load fixtures
# migrate           - Complete data migrations
# load_fixture      - Load fixture data
# runserver         - Start django dev server
# run_listener      - Start the message listener
# run_worker        - Start the general task worker
# run_build_worker  - Start the package build worker
# start             - Start application in Production mode
####

source $HOME/venv/bin/activate

mode=$1
case $mode in
    init)
    init;;

    migrate)
    migrate;;

    runserver)
    runserver;;

    run_listener)
    run_listener;;

    run_worker)
    run_worker;;

    run_build_worker)
    run_build_worker;;

    start|*)
    start;;
esac
