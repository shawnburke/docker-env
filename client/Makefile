
VENV=venv
PYTHON_BIN ?= $(VENV)/bin


$(VENV)/pyvenv.cfg: 
	python3 -m venv $(VENV)
	. $(VENV)/bin/activate; pip install -r requirements.txt;

venv_install: $(VENV)/pyvenv.cfg
	
test: venv_install
	@PATH=$(PYTHON_BIN):$(PATH) cd tests && python3 -m unittest discover

CLIENT_PATH=client/openapi/openapi_client/deault_api.py
openapi: $(CLIENT_PATH)

$(CLIENT_PATH): ../openapi/openapi.yaml venv_install
	if ! which openapi-python-client; then $(PYTHON_BIN)/pip3 install openapi-python-client; fi
	rm -rf docker-env-client
	. $(VENV)/bin/activate; openapi-python-client generate --path ../openapi/openapi.yaml;
	rm -rf lib/docker_env_client
	mv docker-env-client/docker_env_client lib/docker_env_client
	rm -rf docker-env-client


client_gen_openapi: $(CLIENT_PATH)
	
client: client_gen_openapi

.PHONY: test venv_install
