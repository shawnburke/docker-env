FROM golang:1.18.0-alpine3.15


RUN apk update && \
    apk add --no-cache docker-cli python3 && \
    apk add --no-cache --virtual .docker-compose-deps python3-dev libffi-dev openssl-dev gcc libc-dev make && \
    pip3 install docker-compose && \
    apk del .docker-compose-deps

WORKDIR /app

COPY . .

RUN go build -o /app/server .

RUN mkdir -p /data
ENV PORT 3001
ENV DIR "/data"

CMD ["/app/server"]

