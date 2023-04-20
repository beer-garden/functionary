from {{ registry }}/templates/javascript:latest

ARG install_dir=/usr/src/app
COPY --chown=app:app . $install_dir/
WORKDIR $install_dir

RUN npm install
