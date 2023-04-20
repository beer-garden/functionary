#!/bin/bash

PYTHON_VERSION="3.8"
VIRTUALENV="clibuild"
PYTHON="${PYENV_ROOT}/versions/${VIRTUALENV}/bin/python"

function header {
    echo "----------------------------"
    echo $1
    echo "----------------------------"
}

function setup_venv {
    header "Creating virtualenv"
    pyenv --version 2>/dev/null
    if [[ $? -ne 0 ]]; then
        echo "Could not find pyenv. Please install it before proceeding."
        exit 1
    fi

    pyenv install -s $PYTHON_VERSION
    pyenv virtualenv $PYTHON_VERSION $VIRTUALENV
}

function build_whl {
    header "Building whl"
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install --upgrade build setuptools
    $PYTHON -m build --wheel
}

function build_bin {
    header "Building binary"

    # Isolate main.py so that local package is not brought in with it
    mkdir .build
    cp ./src/main.py .build/

    # Install with older urllib3 to ensure CentOS 7 support
    $PYTHON -m pip install ./dist/functionary*.whl pyinstaller "urllib3<2"
    $PYTHON -m PyInstaller ./.build/main.py --name functionary --onefile --collect-all functionary

    # Cleanup
    rm -rf .build
}

function cleanup {
    pyenv virtualenv-delete -f $VIRTUALENV
}

SCRIPT_DIR=$(dirname -- $0)
pushd $SCRIPT_DIR >/dev/null

setup_venv
build_whl
build_bin
cleanup

popd >/dev/null
