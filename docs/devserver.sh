#!/bin/bash

SCRIPT_DIR=$(dirname -- $0)
pushd $SCRIPT_DIR >/dev/null

mkdocs serve \
    --no-directory-urls \
    -a 0.0.0.0:7000

popd >/dev/null
