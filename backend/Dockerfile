FROM golang:1.18.0-alpine3.15


RUN apk update
RUN apk add --no-cache  --update docker-cli python3  python3-dev libffi-dev openssl-dev gcc libc-dev make docker-compose git

WORKDIR /app

COPY backend/go.mod backend/go.sum ./

RUN go mod download

COPY backend .
COPY openapi /openapi

RUN go install github.com/deepmap/oapi-codegen/cmd/oapi-codegen@v1.10.1
RUN mkdir -p .gen/server
RUN oapi-codegen -package openapi_server -generate "types,chi-server" ../openapi/openapi.yaml >.gen/server/server.go
RUN go build -o /app/server .

RUN mkdir -p /data
ENV PORT 3001
ENV DIR "/data"

CMD ["/app/server"]

