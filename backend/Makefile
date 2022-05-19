SERVER_STUB_PATH=backend/.gen/server

GOPATH ?= ~/go

$(GOPATH)/bin/oapi-codegen:
	go install github.com/deepmap/oapi-codegen/cmd/oapi-codegen@v1.10.1


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

start-docker:
	./start -r

server-standup: server_gen_openapi
	@echo "Building images..."
	cd ../workspace-images; ./build-images
	make start-docker
	