
import sys
import shlex

from lib.client import DockerEnvClient
from lib.commands import RootCommand


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

    # # 
    # # destroy instance
    # #
    # parser_destroy = sub_parsers.add_parser(
    #     'destroy', help='destroy an instance')
    # parser_destroy.add_argument(
    #     dest='destroy_name', nargs='?', help='name to instance to destroy')

    # #
    # # Connect via a jumpbox
    # #
    # parser_tunnel = sub_parsers.add_parser('connect', help='tunnel to instance jumpbox')
    # parser_tunnel.add_argument(dest='tunnel_name', help='name of instance')
    # parser_tunnel.add_argument(
    #     dest='tunnel_jumpbox', 
    #     nargs="?", 
    #     help='ssh target of jumpbox instance, e.g. somebox.foo.com or username@somebox')

    # #
    # # SSH shell into instance
    # #
    # parser_ssh = sub_parsers.add_parser(
    #     'ssh', help='open a command prompt to the instance')
    # parser_ssh.add_argument(dest='ssh_name', nargs='?', help='name of instance')



    # args = parser.parse_args()

    
    # if args.command_name == 'ls':
    #     cli.list()
    # elif args.command_name == 'create':
    #     cli.create(args.create_name, password=args.create_password, pubkey_path=args.create_pubkey_path, image=args.create_image)
    # elif args.command_name == 'info':
    #     cli.get(args.info_name)
    # elif args.command_name == 'destroy':
    #     cli.destroy(args.destroy_name)
    # elif args.command_name == 'ssh':
    #     cli.ssh(args.ssh_name)
    # elif args.command_name == 'connect':
    #     cli.connect(args.tunnel_name, args.tunnel_jumpbox)

    # args = parser.parse_args()

    root = RootCommand()

    state = root.exec(None)

    cli = DockerEnvClient(state.data["user"], state.data["host"], state.data["port"])

    if not cli.init():
        print(f'Unable to connect to API host {state.data["host"]} on port {state.data["port"]}')

    # Ensure the host exists and/or SSH to the jumpbox to set it up

    commands = {
        "ls": lambda res: cli.list(),
        "connect": lambda res: cli.connect(res.get("instance")),
        "create": lambda res: cli.create(res.get("name"), res.get("password"), res.get("pubkey_path"), res.get("image")),
        "destroy": lambda res: cli.destroy(res.get("instance")),
    }

    while True:
        print(f'{cli.host}> ', end="")
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
