# functionary development image
# This Dockerfile assumes that the docker-compose.yml in this project is used
# to start things, and thus neede volume mounts etc. will be in place. It is
# not intended as a general purpose Dockerfile.
FROM python:3.10-slim

ARG install_dir=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# initial setup
RUN apt-get -y update && \
    apt-get install -y git make procps curl gcc python3-dev libpq-dev && \
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh && \
    sh /tmp/get-docker.sh && \
    rm /tmp/get-docker.sh

WORKDIR $install_dir
RUN echo "source $HOME/venv/bin/activate" >> $HOME/.bashrc

# pip installs
COPY requirements.txt requirements-dev.txt $install_dir/
RUN python -m venv $HOME/venv && \
    bash -c "source $HOME/venv/bin/activate && pip install --upgrade pip" && \
    bash -c "source $HOME/venv/bin/activate && pip install ipdb debugpy" && \
    bash -c "source $HOME/venv/bin/activate && pip install -r $install_dir/requirements.txt -r $install_dir/requirements-dev.txt"

ENTRYPOINT ["bash", "-c", "source $HOME/venv/bin/activate && python -m debugpy --listen 0.0.0.0:$DEBUG_PORT $WAIT_FOR_CLIENT $DEBUG_CMD"]
