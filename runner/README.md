# Functionary Runner

The runner is the service that actually executes tasks in Functionary. It is
responsible for starting up the package container, executing a function, and
reporting the results back to the core application.

To launch the runner, you need to start two separate processes. Both require
environment variables be set for connecting to the message broker:

- RABBITMQ_USER (required)
- RABBITMQ_PASSWORD (required)
- RABBITMQ_HOST (optional: defaults to localhost)
- RABBITMQ_PORT (optional: defaults to 5672)

Once you have configured the environment, you can run the two process:

## Listener
```shell
LOG_LEVEL=INFO python ./main.py
```

## Worker
```shell
celery -A runner worker --loglevel=INFO
```
