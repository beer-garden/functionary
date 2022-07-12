#!/bin/bash

docker build -t templates/python:latest .

if [[ ! -z "$REGISTRY" ]]; then
    docker tag templates/python:latest ${REGISTRY}/templates/python:latest
fi
