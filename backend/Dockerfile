FROM golang:1.18.0-alpine3.15


RUN apk update
RUN apk add --no-cache  --update docker-cli python3  python3-dev libffi-dev openssl-dev gcc libc-dev make docker-compose

WORKDIR /app

COPY backend/go.mod backend/go.sum ./

RUN go mod download

COPY backend .
COPY openapi /openapi

RUN make docker-env-server
RUN mv docker-env-server /app/server

RUN mkdir -p /data
ENV PORT 3001
ENV DIR "/data"

CMD ["/app/server"]

