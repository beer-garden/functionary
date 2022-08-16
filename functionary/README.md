# Functionary

## Prerequisites

### Dependent Services

To run the various components of Functionary you'll first need the following:

- Redis
- A private container registry

The easiest way to run these is via the docker-compose.yml available
[here](../docker/docker-compose.yml).

```shell
# Starting from the root of the functionary repo
cd docker/
docker compose up -d
```

Authentication to these services within Functionary is not yet configurable. By
default, it will be assumed that these services are accessible via localhost on
their default ports. If they are located elsewhere, you can configure that via
environment variables:

- REDIS_HOST
- REDIS_PORT
- REGISTRY_HOST
- REGISTRY_PORT

### Base Image Templates

Packages in Functionary get converted into docker images, which are then
launched as containers when executing a task. The base images for these package
docker images are referred to as templates, and must be built and pushed to the
private registry before Functionary will be able to build packages.

A helper script is available to build and push the images. Make sure your
registry is started before running the script.

```shell
# Starting from the root of the functionary repo
cd templates
./build.sh -p
```

If your registry is not located at `localhost:5000`, you can specify the
location using the environment variables described earlier.

## Developer Setup

**NOTE:** These instructions are intended for developers who are looking to get
started working on Functionary. Instructions for general users will be added as
the project matures.

### Python Requirements

Functionary is being developed with containers being the primary target for
deployment. As such, the intention is to officially support only the latest
minor version of python (e.g. The latest 3.X). Be sure to keep this in mind if
you are intending to run the application locally while developing.

### Django Setup

Install the requirements like so:

```shell
pip install -r requirements.txt -r requirements-dev.txt
```

Generate the migrations:

```shell
./manage.py makemigrations
```

Run the migrations:

```shell
./manage.py migrate
```

Create a superuser:

```shell
./manage.py createsuperuser
```

## Run the Server

To start the server, run:

```shell
DEBUG=TRUE DJANGO_SECRET_KEY=supersecret ./manage.py runserver 8000
```

The `DJANGO_SECRET_KEY` is arbitrary and the `8000` at the end is the port
number to listen on. It can be freely changed to anything.

## Start the build worker

When a package is published, the actual work of building the image is handed off
to a separate builder process. To start that process:

```shell
LOG_LEVEL=INFO ./manage.py run_build_worker
```

## Start the function runner

Tasks get executed via a separate runner service. Information on the runner can
be found [here](../runner/README.md).

## Access the Server

The links below assume Functionary is running on `localhost:8000`. Be sure to
use the host name and port number appropriate to your setup.

- [Django admin pages](http://localhost:8000/admin)
- [Browsable API](http://localhost:8000/api/v1)
- [Swagger](http://localhost:8000/api/docs/swagger)
- [ReDoc](http://localhost:8000/api/docs/redoc)
