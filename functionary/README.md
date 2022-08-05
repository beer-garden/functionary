# Functionary

## Setup

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
number to listen on. It can freely be changed to anything.

## Start the build worker

When a package is published, the actual work of building the image is handed off
to a separate builder process. To start that process:

```shell
LOG_LEVEL=INFO ./manage.py run_build_worker
```

## Access the Server

The URLS below assume a default port of `8000`. Be sure to use the appropriate
port number.

- Django admin pages: [http://localhost:8000/admin](http://localhost:8000/admin)
- Browsable API: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- Swagger:
  [http://localhost:8000/api/docs/swagger](http://localhost:8000/api/docs/swagger)
- ReDoc:
  [http://localhost:8000/api/docs/redoc](http://localhost:8000/api/docs/redoc)
