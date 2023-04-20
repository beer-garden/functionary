#!/bin/sh
# Simpler version of the build.sh for use with the CI/CD pipelin

usage() {
    echo "Usage:"
    echo "  simple_build.sh <registry> <release>"
    exit 1
}

if [ "$1" = "" ]; then
    usage
fi

if [ "$2" = "" ]; then
    usage
fi

registry=$(echo $1 | sed '/\/$/!s/$/\//')
version=$2

# -------------------------
# Begin django builds
# -------------------------
components="builder cli listener scheduler webserver worker"
for component in $components; do
    tag=${registry}${component}:${version}
    echo "Building $tag"

    docker build -f ./functionary.Dockerfile --target $component -t $tag ../
    docker push $tag
done
# -------------------------
# End django builds
# -------------------------

# -------------------------
# Begin runner build
# -------------------------
tag=${registry}runner:${version}
echo "Building $tag"
docker build -f ./runner.Dockerfile -t $tag ../runner
docker push $tag
# -------------------------
# End runner build
# -------------------------

# -------------------------
# Begin source build
# -------------------------
tag=${registry}source:${version}
echo "Building $tag"
docker build -f ./source.Dockerfile -t $tag ../
docker push $tag
# -------------------------
# End source build
# -------------------------
