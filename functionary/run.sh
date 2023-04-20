#!/bin/bash

# Run script for app in Docker container

##########################
# User defined functions #
##########################

makemigrations() {
    python manage.py makemigrations
}

migrate() {
    python manage.py migrate
}

load_fixtures_prod() {
    python manage.py loaddata bootstrap_prod
}

load_fixtures_dev() {
    python manage.py loaddata bootstrap_dev
}

create_vhost() {
    # Temporary manual creation of runner vhost. Remove once runner registration
    # is implemented
    python manage.py shell -c "from core.utils.rabbitmq import create_vhost; create_vhost('public')"
}

init_dev() {
    makemigrations
    migrate
    load_fixtures_dev
    create_vhost
}

init_prod() {
    migrate
    load_fixtures_prod
    create_vhost
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

run_scheduler() {
    python manage.py run_scheduler
}

run_builder() {
    python manage.py run_builder
}

start() {
    if [[ ${SKIP_INIT} -ne 1 ]]; then
        migration_status=$(python manage.py showmigrations)
        migrations_run=$(echo "${migration_status}" | grep "\[X\]" | wc -l)
        
        if [[ ${migrations_run:-0} -eq 0 ]]; then
            echo "No migrations run, initializing database"
            init_prod
        fi
    fi
    gunicorn --bind=${BIND_ADDRESS:-0.0.0.0} --workers=${NUM_WORKERS:-4} functionary.wsgi
}

######################
# Script starts here #
######################

####
# Expected run modes (passed in via docker run cmd)
#
# init_dev          - Initialize a dev environment
# init_prod         - Initialize a prod environment
# migrate           - Complete data migrations
# runserver         - Start django dev server
# run_listener      - Start the message listener
# run_scheduler     - Start the task scheduler
# run_worker        - Start the general task worker
# run_builder       - Start the package build worker
# start             - Start application in Production mode
####

source $HOME/venv/bin/activate

mode=$1
case $mode in
init_dev)
    init_dev
    ;;

init_prod | init)
    init_prod
    ;;

migrate)
    migrate
    ;;

runserver)
    runserver
    ;;

run_builder)
    run_builder
    ;;

run_listener)
    run_listener
    ;;

run_worker)
    run_worker
    ;;

run_scheduler)
    run_scheduler
    ;;

start | *)
    start
    ;;
esac
