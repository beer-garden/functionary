FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/
ENV SSL_CERT_DIR /etc/ssl/certs/

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

RUN adduser --shell /bin/false --disabled-password --gecos "" --uid 1001 app && \
    chown -R app:app /usr/src/app

COPY --chmod=644 .certs/. /etc/ssl/certs/
COPY --chown=app:app python/requirements.txt python/*.py ./

USER app

RUN pip --no-cache-dir install -r ./requirements.txt

ENTRYPOINT ["python", "main.py"]