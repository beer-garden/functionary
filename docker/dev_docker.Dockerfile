# functionary development image
# This Dockerfile assumes that the docker-compose.yml in this project is used
# to start things, and thus neede volume mounts etc. will be in place. It is
# not intended as a general purpose Dockerfile.
FROM python:3.11-slim

ARG install_dir=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# initial setup
RUN apt-get update && \
    apt-get install -y \
    # python build deps
    make gcc python3-dev libpq-dev \
    # packages for docker install
    ca-certificates curl gnupg lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y docker-ce containerd.io

WORKDIR $install_dir
RUN echo "source $HOME/venv/bin/activate" >> $HOME/.bashrc

# pip installs
COPY requirements.txt requirements-dev.txt $install_dir/
RUN python -m venv $HOME/venv && \
    bash -c "source $HOME/venv/bin/activate && pip install --upgrade pip" && \
    bash -c "source $HOME/venv/bin/activate && pip install -r $install_dir/requirements.txt -r $install_dir/requirements-dev.txt"

ENTRYPOINT ["./run.sh"]
CMD ["start"]
