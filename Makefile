


openapi: $(SERVER_STUB_PATH)/server.go $(CLIENT_PATH)

backend/docker-env-server: openapi
	cd backend; go build -o docker-env-server .

openapi:
	make -C backend openapi
	make -C client openapi

test: 
	@echo "Server tests"
	make -C backend test
	@echo "Client tests"
	make -C client test

server-standup:
	make -C backend server-standup