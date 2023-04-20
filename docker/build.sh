#!/bin/bash

SCRIPT_DIR=$(dirname -- $0)
pushd $SCRIPT_DIR >/dev/null

latest="false"
push="false"
registry=""
echo=""
images=()

function usage {
    echo ""
    echo "Usage:  build.sh [OPTIONS] <VERSION>"
    echo ""
    echo "Build container images for a release of Functionary."
    echo ""
    echo "Options:"
    echo "  -d, --dry-run      Echo commands that would be run, but do not execute them."
    echo "  -l, --latest       Tag the images with 'latest' in addition to the version number."
    echo "  -p, --publish      Publish to the registry after building."
    echo "  -r, --registry     Container registry host, port and namespace. e.g. localhost:5000/functionary"
    exit 1
}

function tag_as_latest {
    tag=$1
    latest_tag=$(echo $tag | sed "s/:$version\$/:latest/")

    $echo docker tag $tag $latest_tag
    images+=($latest_tag)
}

VALID_ARGS=$(getopt --name build.sh -o dhlpr: --long dry-run,help,latest,publish,registry: -- "$@")
if [[ $? -ne 0 ]]; then
    usage
fi

eval set -- "${VALID_ARGS}"
while true; do
    case "$1" in
    -d | --dry-run)
        echo="echo"
        shift
        ;;
    -l | --latest)
        latest="true"
        shift
        ;;
    -p | --publish)
        push="true"
        shift
        ;;
    -r | --registry)
        # append / to the registry name if not present
        registry=$(echo $2 | sed '/\/$/!s/$/\//')
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

if [[ "$1" = "" ]]; then
    echo "Release version number is required"
    usage
fi

version=$1

# -------------------------
# Begin django builds
# -------------------------
components=("builder" "cli" "listener" "scheduler" "webserver" "worker")
for component in ${components[@]}; do
    tag=${registry}${component}:${version}
    echo "Building $tag"

    $echo docker build -f ./functionary.Dockerfile --target $component -t $tag ../
    images+=($tag)

    if [[ "$latest" = "true" ]]; then
        tag_as_latest $tag
    fi
done
# -------------------------
# End django builds
# -------------------------

# -------------------------
# Begin runner build
# -------------------------
tag=${registry}runner:${version}
echo "Building $tag"
$echo docker build -f ./runner.Dockerfile -t $tag ../runner
images+=($tag)

if [[ "$latest" = "true" ]]; then
    tag_as_latest $tag
fi
# -------------------------
# End runner build
# -------------------------

# -------------------------
# Begin source build
# -------------------------
tag=${registry}source:${version}
echo "Building $tag"
$echo docker build -f ./source.Dockerfile -t $tag ../
images+=($tag)

if [[ "$latest" = "true" ]]; then
    tag_as_latest $tag
fi
# -------------------------
# End source build
# -------------------------

if [[ "$push" = "true" ]]; then
    for image in ${images[@]}; do
        echo "Pushing $image"
        $echo docker push $image
    done
fi

popd >/dev/null
