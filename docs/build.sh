#!/bin/bash

function usage {
    echo "Usage: build.sh <output_path>"
    exit 1
}

if [[ $# -ne 1 ]]; then
    usage
fi

TARGET_DIR=$(readlink -f $1)

SCRIPT_DIR=$(dirname -- $0)
pushd $SCRIPT_DIR >/dev/null

mkdocs build \
    --no-directory-urls \
    --site-dir ${TARGET_DIR}

popd >/dev/null
