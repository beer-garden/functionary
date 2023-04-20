# Dockerfile for building images of the django components.
# Build context should be the base repo directory.

# documentation image
FROM python:3.11-slim AS docs
ARG docs_dir=/docs/src
ARG build_dir=/docs/build
COPY ./docs $docs_dir
WORKDIR $docs_dir
RUN pip install -r requirements.txt && \
    ./build.sh $build_dir


# cli image
FROM centos:7 AS cli
RUN BUILD_DEPS="git gcc make patch zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel xz-devel" && \
    yum install -y $BUILD_DEPS && \
    curl https://pyenv.run | bash

COPY ./cli /cli
WORKDIR /cli
RUN export PYENV_ROOT="$HOME/.pyenv" && \
    export PATH="$PYENV_ROOT/bin:$PATH" && \
    eval "$(pyenv init -)" && \
    ./build.sh

ENTRYPOINT ["./dist/functionary"]


# functionary django image
FROM python:3.11-slim AS django_base

ARG user=functionary
ARG install_dir=/app

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE "functionary.settings.prod"

RUN useradd -l -m $user && \
    mkdir -p $install_dir

COPY ./functionary $install_dir/
RUN chown $user:$user -R $install_dir

RUN BUILD_DEPS="make gcc python3-dev libpq-dev libldap2-dev libsasl2-dev" && \
    PYTHON_DEPS="libpq5" && \
    apt-get update && \
    apt-get install -y $BUILD_DEPS $PYTHON_DEPS --no-install-recommends && \
    su - $user -c 'echo "source $HOME/venv/bin/activate" >> $HOME/.bashrc' && \
    su - $user -c 'python -m venv $HOME/venv' && \
    su - $user -c "bash -c 'source /home/$user/venv/bin/activate && pip install --upgrade pip'" && \
    su - $user -c "bash -c 'source /home/$user/venv/bin/activate && pip install -r $install_dir/requirements.txt'" && \
    apt-get purge -y --auto-remove $BUILD_DEPS

WORKDIR $install_dir
USER $user

ENTRYPOINT ["./run.sh"]

FROM django_base as listener
CMD ["run_listener"]

FROM django_base as worker
CMD ["run_worker"]

FROM django_base as scheduler
CMD ["run_scheduler"]

FROM django_base as webserver
COPY --from=docs /docs/build $install_dir/ui/static/docs
COPY --from=cli /cli/dist/functionary $install_dir/ui/static/utils/
RUN mkdir $install_dir/static && \
    bash -c "source $HOME/venv/bin/activate && \
    mkdir ./core/static && ./manage.py spectacular --file ./core/static/functionary.yaml && \
    ./manage.py collectstatic"
CMD ["start"]

FROM django_base as builder
USER root
RUN echo "source $HOME/venv/bin/activate" >> $HOME/.bashrc && \
    apt-get install -y \
    ca-certificates curl gnupg lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y docker-ce containerd.io
COPY --from=django_base /home/$user/venv/ /root/venv/
CMD ["run_builder"]
