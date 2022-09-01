# Functionary Runner

The runner is the service that actually executes tasks in Functionary. It is
responsible for starting up the package container, executing a function, and
reporting the results back to the core application.

To launch the runner, you need to start two separate processes:

```shell
# required env variables
export RABBITMQ_USER=someuser
export RABBITMQ_PASSWORD=greatpassword

# start the listener
LOG_LEVEL=INFO python ./main.py

# start the worker
celery -A runner worker --loglevel=INFO
```
