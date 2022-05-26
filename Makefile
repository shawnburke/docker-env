

install:
	$(MAKE) -c backend install
	$(MAKE) -c client install


backend/docker-env-server: openapi
	cd backend; go build -o docker-env-server .

openapi:
	$(MAKE) -C backend openapi
	$(MAKE) -C client openapi

test: 
	@echo "Server tests"
	$(MAKE) -C backend test
	@echo "Client tests"
	$(MAKE) -C client test

images:
	cd workspace-images && ./build-images

standup:
	$(MAKE) -C backend start-docker