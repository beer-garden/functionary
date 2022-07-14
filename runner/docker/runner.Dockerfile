# package_runner dockerfile
FROM python:3.10-slim

ENV INSTALL_DIR /opt/package_runner
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# initial setup
RUN mkdir -p $INSTALL_DIR/app

# pip installs
COPY requirements.txt $INSTALL_DIR/
RUN python -m venv $INSTALL_DIR/venv && \
    bash -c "source $INSTALL_DIR/venv/bin/activate && pip install --upgrade pip" && \
    bash -c "source $INSTALL_DIR/venv/bin/activate && pip install ipdb remote-pdb" && \
    bash -c "source $INSTALL_DIR/venv/bin/activate && pip install -r $INSTALL_DIR/requirements.txt"

COPY main.py $INSTALL_DIR/app/
COPY package_runner $INSTALL_DIR/app/package_runner

COPY docker/docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
