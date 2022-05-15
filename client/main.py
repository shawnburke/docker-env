
import sys
import shlex

import lib
from lib.client import DockerEnvClient
from lib.commands import RootCommand
from lib.container import Container



container = Container({
    lib.Printer: lib.Printer(),
    lib.SSH: lib.SSH,
    lib.Tunnel: lib.Tunnel,
    lib.Connection: lib.Connection,
    lib.API: lib.API
})

if __name__ == '__main__':


    # docker-env [api host] => connects to a host
    #
    # > ls => list instances
    #
    # > create my-instance => create new instance (returns the port and the jumpbox, or null if same as host)
    #       Created my-instance
    #           SSH-port: 1234
    #       
    # 
    # > connect my-instance (connects to ssh, e.g. ssh -NL SSH_PORT:localhost:SSH_PORT jumpbox|host)  
    #       SSH is          localhost:50022
    #       VSCode Brower   http://localhost:50030 (password=afasfa34134)
    #
    #       * periodically polls for other ports, if found, it connect to them eg ssh -p SSH_PORT -NL PORT:localhost:PORT user@localhost
    #       * Announces "Connected my-instance VSCode Browser as port 1234"

    root = RootCommand()

    state = root.exec(None)

    cli = DockerEnvClient(container, state.data["user"], state.data.get("jumpbox", "localhost"), state.data["port"])

    if not cli.init():
        print(f'Unable to connect to API host {state.data["host"]} on port {state.data["port"]}')

    # Ensure the host exists and/or SSH to the jumpbox to set it up

    commands = {
        "ls": lambda res: cli.list(),
        "connect": lambda res: cli.connect(res.get("instance")),
        "create": lambda res: cli.create(res.get("name"), res.get("password"), res.get("pubkey_path"), res.get("image")),
        "destroy": lambda res: cli.destroy(res.get("instance")),
        "disconnect": lambda res: cli.disconnect(res.get("instance")),
        "ssh": lambda res: cli.ssh(res.get("instance")),
        "info": lambda res: cli.get(res.get("instance")),
        "restart": lambda res: cli.restart(res.get("instance")),
        "quit": lambda res: cli.stop()
    }

    try:
        while True:
            print(f'{cli.host}> ', end="", flush=True)
            line = sys.stdin.readline()
            line = line.rstrip()

            args = shlex.split(line)

            if len(args) == 0:
                continue

            command = root.find(args[0])
            if command is None:
                continue

            result = command.exec(args[1:])

            if result is None:
                continue

            target = commands.get(result.command)

            if target is None:
                print(f' Unknown command: {command}')
                continue

            target(result)
    except KeyboardInterrupt:
        cli.stop()
