#! /bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
if [ "$1" == "launch" ]
then
	while true
	do
		mkdir -p ~/.log
		code-server --auth none --bind-addr 0.0.0.0:8080 >> ~/.log/code-server.log
	done
fi

nohup $SCRIPT_DIR/start-code-server.sh launch &


