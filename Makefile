SERVER_STUB_PATH=backend/.gen/server


$(GOPATH)/bin/oapi-codegen:
	go install github.com/deepmap/oapi-codegen/cmd/oapi-codegen@v1.10.1


$(SERVER_STUB_PATH)/server.go: openapi/openapi.yaml $(GOPATH)/bin/oapi-codegen
	mkdir -p $(SERVER_STUB_PATH)
	$(GOPATH)/bin/oapi-codegen -package openapi_server -generate "types,chi-server" openapi/openapi.yaml >$(SERVER_STUB_PATH)/server.go


client/lib/openapi.py: openapi/openapi.yaml
	docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli generate \
		-i /local/openapi/openapi.yaml \
		-g python \
		-o /local/client/lib/openapi.py

openapi: $(SERVER_STUB_PATH)/server.go client/lib/openapi.py