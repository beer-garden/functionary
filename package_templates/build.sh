#!/bin/bash
#
# Script for building package templates and publishing them to private registry

SCRIPT_DIR=$(dirname -- $0)
pushd $SCRIPT_DIR >/dev/null
push="false"
cacerts=()
certdir=".certs"
registry="localhost:5000"
languages=()

function usage {
    echo ""
    echo "Usage:  build.sh [OPTIONS]"
    echo ""
    echo "Build package templates and publish them to the registry"
    echo ""
    echo "Options:"
    echo "  -c, --cacerts      Path to a file or folder containing CA certs to include in the template"
    echo "  -l, --language     Build only the specified language template"
    echo "  -p, --publish      Publish to the registry after building"
    echo "  -r, --registry     Container registry host and port. Defaults to localhost:5000."
    exit 1
}

function copy_certs {
    # Always mkdir, since the Dockerfiles don't support conditional logic and
    # always assume its there
    mkdir $certdir 2>/dev/null

    for path in ${cacerts[@]}; do
        if [[ -d "${path}" ]]; then
            cp ${path}/* $certdir/
        else
            cp ${path} $certdir/
        fi
    done
}

function cleanup {
    rm -rf $certdir
}

VALID_ARGS=$(getopt --name build.sh -o c:hl:pr: --long cacerts:,help,language:,publish,registry: -- "$@")
if [[ $? -ne 0 ]]; then
    usage
fi

eval set -- "${VALID_ARGS}"
while true; do
    case "$1" in
    -c | --cacerts)
        cacerts+=($2)
        shift 2
        ;;
    -l | --language)
        ls $2.Dockerfile &>/dev/null
        if [[ $? -ne 0 ]]; then
            echo "Unrecognized language $2"
            exit 1
        fi

        languages+=($2)
        shift 2
        ;;
    -p | --publish)
        push="true"
        shift
        ;;
    -r | --registry)
        registry=$2
        shift 2
        ;;
    --)
        shift
        break
        ;;
    *)
        usage
        ;;
    esac
done

if [[ ! ${languages[@]} ]]; then
    # No languages specified, so load them all
    languages=$(ls -1 *.Dockerfile | sed "s/.Dockerfile//")
fi

copy_certs

for lang in ${languages[@]}; do
    docker build -f ${lang}.Dockerfile -t ${registry}/templates/${lang}:latest .

    if [[ "$push" = "true" ]]; then
        docker push ${registry}/templates/${lang}:latest
    fi
done

cleanup
popd >/dev/null
