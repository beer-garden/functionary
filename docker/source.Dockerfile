# Dockerfile with all of the source from repo, plus pyenv and virtualenvs
# for each component.
#
# Build context should be the base repo directory.
FROM python:3.11-slim

ARG install_dir=/opt/functionary
ARG venv_dir=/opt/venv

ENV PYTHONUNBUFFERED 1

RUN mkdir -p $install_dir $venv_dir

COPY . $install_dir/

RUN BUILD_DEPS="make gcc python3-dev libpq-dev libldap2-dev libsasl2-dev" && \
    PYTHON_DEPS="libpq5" && \
    OPTS="git ssh vim-tiny" && \
    apt-get update && \
    apt-get install -y $BUILD_DEPS $PYTHON_DEPS $OPTS --no-install-recommends && \
    python -m venv $venv_dir/cli && \
    $venv_dir/cli/bin/python -m pip install \
    -r $install_dir/cli/requirements.txt \
    -r $install_dir/cli/requirements-dev.txt && \
    python -m venv $venv_dir/functionary && \
    $venv_dir/functionary/bin/python -m pip install \
    -r $install_dir/functionary/requirements.txt \
    -r $install_dir/functionary/requirements-dev.txt && \
    python -m venv $venv_dir/runner && \
    $venv_dir/runner/bin/python -m pip install \
    -r $install_dir/runner/requirements.txt \
    -r $install_dir/runner/requirements-dev.txt && \
    apt-get purge -y --auto-remove $BUILD_DEPS

WORKDIR $install_dir

ENTRYPOINT ["/bin/bash"]
