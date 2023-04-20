from {{ registry }}/templates/python:latest

ARG install_dir=/usr/src/app
COPY --chown=app:app . $install_dir/
WORKDIR $install_dir

RUN pip --no-cache-dir install -r requirements.txt
