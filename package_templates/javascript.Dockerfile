FROM node:lts-buster-slim

ENV SSL_CERT_DIR /etc/ssl/certs/

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

RUN adduser --shell /bin/false --disabled-password --gecos "" --uid 1001 app && \
    chown -R app:app /usr/src/app

COPY --chmod=644 .certs/. /etc/ssl/certs/
COPY --chown=app:app javascript/package.json javascript/*.js ./
RUN ls -l

USER app

RUN npm install

ENTRYPOINT ["node", "main.js"]