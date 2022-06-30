FROM node:lts-buster-slim

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

RUN addgroup --gid 1001 --system app && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app

USER app

COPY package.json *.js ./

RUN npm install || true

ENTRYPOINT ["node", "main.js"]
