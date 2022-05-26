
all: client server

install:
	$(MAKE) -c backend install
	$(MAKE) -c client install

client: 
	$(MAKE) -C client openapi

server:
	$(MAKE) -C backend server	

test: 
	@echo "Server tests"
	$(MAKE) -C backend test
	@echo "Client tests"
	$(MAKE) -C client test

images:
	cd workspace-images && ./build-images

standup: images
	$(MAKE) -C backend start-docker

.PHONY: openapi all