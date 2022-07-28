from {{ registry }}/templates/python:latest

ARG install_dir=/usr/src/app
COPY . $install_dir/
WORKDIR $install_dir

USER root
RUN pip install -r requirements.txt

USER app
