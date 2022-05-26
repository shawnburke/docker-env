
VENV=venv
PYTHON_BIN ?= $(VENV)/bin

$(VENV)/pyvenv.cfg: 
	python3 -m venv $(VENV)

install: $(VENV)/pyvenv.cfg
	. $(VENV)/bin/activate; python3 setup.py install;

package:
	. $(VENV)/bin/activate; if [ ! which twine ]; then pip3 install twine; fi
	@PATH="$(PYTHON_BIN):$(PATH)" python3 setup.py sdist && twine check dist/*
	
CLIENT_PATH=docker_env_client/lib/api_client/client.py

test: $(CLIENT_PATH)
	@PATH="$(PYTHON_BIN):$(PATH)" python3 -m unittest discover
	
$(CLIENT_PATH): ../openapi/openapi.yaml
	if ! which openapi-python-client; then $(PYTHON_BIN)/pip3 install openapi-python-client; fi
	rm -rf docker-env-client
	. $(VENV)/bin/activate; openapi-python-client generate --path ../openapi/openapi.yaml;
	rm -rf docker_env_client/lib/api_client
	mv docker-env-client/docker_env_client docker_env_client/lib/api_client
	rm -rf docker-env-client

openapi: $(CLIENT_PATH)

.PHONY: test venv_install
