#!/bin/bash

# Init script to execute follow on configurations after the functionary-django container has been launched


activate_python_venv() {
    source $HOME/venv/bin/activate
}

migrate() {
    python manage.py migrate
}

load_fixture() {
    if [ -n "$1" ]; then
        python manage.py loaddata $1
    else
        echo "No fixture supplied"
    fi
}


activate_python_venv
migrate
load_fixture bootstrap
