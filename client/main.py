from abc import abstractmethod
import argparse
import sys
import shlex
import os
from lib.client import DockerEnvClient
from lib.commands import RootCommand


if __name__ == '__main__':

    #
    # docker-env ls => list instances
    # docker-env create my-instance => create new instance
    #       Created my-instance
    #           SSH-port: 1234
    #       run 'docker-env connect' to set up tunnels
    # 
    # docker-env connect my-instance
    #       SSH is          localhost:50022
    #       VSCode Brower   http://localhost:50030 (password=afasfa34134)
    #
    # docker-env ssh => connect and forward ssh: ssh -A -p 50022 user@localhost
    # 
    # connect IntelliJ or VSCode SSH => localhost:50022

    # host=os.environ.get("HOST", "localhost")
    # port=os.environ.get("PORT", default_port)
  
    # # create the top-level parser
    # parser = argparse.ArgumentParser(prog='docker-env')
    # parser.add_argument('--host', action='store', default=host,
    #                     help='Server hostname')
    # parser.add_argument('--port', action='store', default=port,
    #                     help='Port to contact server')
    # parser.add_argument('--user', dest="user", action='store', default=os.environ["USER"],
    #                     help='Username to use')
    # parser.add_argument("jumpbox", dest="jumpbox", action='store',nargs="?", help='SSH jumpbox or config')

    # # create sub-parser
    # sub_parsers = parser.add_subparsers(
    #     help='command help', dest="command_name")

    # #
    # # CREATE Instance
    # #
    # parser_create = sub_parsers.add_parser(
    #     'create', help='create new instance')
    # parser_create.add_argument(
    #     dest='create_name', nargs="?", help='Name of instance to create')
    # parser_create.add_argument(
    #     '--password', dest="create_password", help='instance password, required if no pubkey avaiable')
    # parser_create.add_argument(
    #     '--pubkey', dest="create_pubkey_path", help='pubkey path',default=f'{os.environ["HOME"]}/.ssh/id_rsa.pub')
    # parser_create.add_argument(
    #     '--image', dest="create_image", default='docker-env-full:local', help='instance image. Must have SSH avaialble over port 22.')
    
    
    # #
    # # List instances
    # #

    # parser_ls = sub_parsers.add_parser(
    #     'ls', help='list current instances')

    # parser_info = sub_parsers.add_parser(
    #     'info', help='get instance detail')
    # parser_info.add_argument(
    #     dest='info_name', nargs='?', help='name of instance')

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

    # if not args.host and not args.jumpbox:
    #     print("Must supply either jumpbox or --host")
    #     sys.exit(1)


    # repl args
        # connect [jumpbox] => connected to API on port 1234
        #     ls => instances

    # commands = {
    #     "ls": {
    #         "command": lambda cmd, args:  print(f'NYI: {cmd}'),
    #     },
    #     "create": {
    #         "command": lambda cmd, args:  print(f'NYI: {cmd}'),
    #     }
    # }


    root = RootCommand()

    state = root.exec(None)

    cli = DockerEnvClient(state.data["user"], state.data["host"], state.data["port"])

    if not cli.init():
        print(f'Unable to connect to API host {state.data["host"]} on port {state.data["port"]}')

    # Ensure the host exists and/or SSH to the jumpbox to set it up

    while True:
        print("> ", end="")
        line = sys.stdin.readline()
        
        line = line.rstrip()

        args = shlex.split(line)
        command = root.find(args[0])
        if command is None:
            continue

        result = command.exec(args[1:])

        if result.command == "ls":
            cli.list()






       # parser_tunnel = sub_parsers.add_parser('connect', help='tunnel to instance jumpbox')
    # parser_tunnel.add_argument(dest='tunnel_name', help='name of instance')
    # parser_tunnel.add_argument(
    #     dest='tunnel_jumpbox', 
    #     nargs="?", 
    #    