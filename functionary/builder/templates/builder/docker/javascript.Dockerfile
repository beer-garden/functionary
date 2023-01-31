from {{ registry }}/templates/javascript:latest

ARG install_dir=/usr/src/app
COPY . $install_dir/
WORKDIR $install_dir

USER app
