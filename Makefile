SERVER_STUB_PATH=backend/.gen/server


$(GOPATH)/bin/oapi-codegen:
	go install github.com/deepmap/oapi-codegen/cmd/oapi-codegen@v1.10.1


$(SERVER_STUB_PATH)/server.go: openapi/openapi.yaml $(GOPATH)/bin/oapi-codegen
	mkdir -p $(SERVER_STUB_PATH)
	$(GOPATH)/bin/oapi-codegen -package openapi_server -generate "types,chi-server" openapi/openapi.yaml >$(SERVER_STUB_PATH)/server.go


CLIENT_PATH=client/openapi/openapi_client/deault_api.py

$(CLIENT_PATH): openapi/openapi.yaml
	if ! which openapi-python-client; then pip3 install openapi-python-client; fi
	cmd=generate
	if [ -d docker-env-client-client ];\
		then openapi-python-client update --path openapi/openapi.yaml; \
		else openapi-python-client generate --path openapi/openapi.yaml;  \
		fi
	rm -rf client/lib/docker_env_client
	mv docker-env-client/docker_env_client client/lib/docker_env_client
	

openapi: $(SERVER_STUB_PATH)/server.go $(CLIENT_PATH)