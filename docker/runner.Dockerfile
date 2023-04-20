# functionary runner image
FROM python:3.11-slim

ARG install_dir=/app

ENV PYTHONUNBUFFERED 1
ENV RUNNER_DEFAULT_VHOST public

RUN apt-get update && \
    apt-get install -y \
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
COPY requirements.txt $install_dir/
RUN python -m venv $HOME/venv && \
    bash -c "source $HOME/venv/bin/activate && pip install --upgrade pip" && \
    bash -c "source $HOME/venv/bin/activate && pip install -r $install_dir/requirements.txt"

COPY . /app

ENTRYPOINT ["./run.sh"]
CMD ["start"]
