SERVER_STUB_PATH=.gen/server

GOPATH ?= ~/go

$(GOPATH)/bin/oapi-codegen:
	go install github.com/deepmap/oapi-codegen/cmd/oapi-codegen@v1.10.1

install: openapi
	go mod download

SERVER_STUB_FILE=$(SERVER_STUB_PATH)/server.go
openapi: $(SERVER_STUB_FILE) ../openapi/openapi.yaml $(GOPATH)/bin/oapi-codegen
	mkdir -p $(SERVER_STUB_PATH)
	$(GOPATH)/bin/oapi-codegen -package openapi_server -generate "types,chi-server" ../openapi/openapi.yaml >$(SERVER_STUB_FILE)

server: docker-env-server

docker-env-server: openapi
	go build -o docker-env-server .

test:
	go test ./...

start: docker-env-server
	./docker-env-server


TAG ?= docker-env-server:local
docker-build:
	cd .. && docker build -t $(TAG) -f backend/Dockerfile .

start-docker: docker-build
	./start -r -d
	echo "Server is now running as daemon, tailing logs... (you can quit this)"
	docker logs -f docker-env-server
	
