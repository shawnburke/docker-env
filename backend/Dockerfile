# NOTE THIS MUST BE RUN FROM THE REPO ROOT CONTEXT (cd .. && docker-build -t tag -f backend/Dockerfile .)

FROM golang:1.18.0-alpine3.15

RUN apk update
RUN apk add --no-cache  --update docker-cli python3  python3-dev libffi-dev openssl-dev gcc libc-dev make docker-compose git

WORKDIR /app
COPY backend/go.mod backend/go.sum ./
RUN go mod download

COPY backend .
COPY openapi /openapi

RUN make -e "GOPATH=/go" docker-env-server

RUN mkdir -p /data
ENV PORT 3001
ENV DIR "/data"

CMD ["/app/docker-env-server"]

