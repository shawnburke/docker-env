
from abc import abstractmethod
import argparse
from dataclasses import dataclass
import os

DEFAULT_PORT=3001

@dataclass
class CommandResult:
    command: str
    data: object

    def get(self, field, default=None):
        if hasattr(self.data, field):
            return getattr(self.data, field,default)
        return self.data.get(field, default)
class Command:
    def __init__(self, name, commands = None):
        self.name = name
        self.commands = commands

    def exec(self, args) -> 'CommandResult':
        parser = self.parser()

        parsed = {}

        if parser is not None:
            parsed = parser.parse_args(args)
        return self.command(self.name, parsed)

    @abstractmethod
    def parser(self):
        pass


    def command(self, name, args) -> 'CommandResult':
        if isinstance(name, list):
            name = name[0]
        return CommandResult(name, args)

    def handles(self, cmd):
        names = self.name
        if not isinstance(self.name, list):
            names = [self.name]

        for n in names:
            if cmd == n:
                return True
        
        return False

    def find(self, cmd) -> 'Command':
        a = []
        for c in self.commands:
            a.append(str(c.name))
            if c.handles(cmd):
                return c
        av = ""

        if len(a) > 0:
            av = f'try: {",".join(a)}'
        print(f'Unknown command "{cmd}". {av}')




class RootCommand(Command):

    def __init__(self):
        super().__init__("root",[
            ListCommand(),
            HelpCommand(),
            CreateCommand(),
            InfoCommand(),
            RestartCommand(),
            ConnectCommand(),
            DisconnectCommand(),
            SSHCommand(),
            DestroyCommand(),
            QuitCommand(),
        ] )


    def parser(self):

        host=os.environ.get("HOST", "localhost")
        port=os.environ.get("PORT", DEFAULT_PORT)

        # create the top-level parser
        parser = argparse.ArgumentParser(prog='docker-env')
        parser.add_argument('--host', action='store', default=host,
                            help='Server hostname')
        parser.add_argument('--port', action='store', default=port,
                            help='Port to contact server')
        parser.add_argument('--user', dest="user", action='store', default=os.environ["USER"],
                            help='Username to use')
        parser.add_argument("jumpbox", action='store',nargs="?", help='SSH jumpbox or config')
        return parser

    def command(self, name, args):
        return CommandResult("root", {
            "jumpbox": args.jumpbox,
            "host": args.host,
            "port": args.port,
            "user": args.user,
        })
    

class ListCommand(Command):
    def __init__(self):
        super().__init__( "ls")

    def parser(self):
        return None

class HelpCommand(Command):
    def __init__(self):
        super().__init__(["help", "?"])

    def parser(self):
        return None

    def command(self, name, args) -> 'CommandResult':
        print("Available commands: ls, create, info, ssh, connect, disconnect, destroy, quit")
        return None


class QuitCommand(Command):
    def __init__(self):
        super().__init__(["quit", "exit"])

    def parser(self):
        print("Cleaning up tunnels...")
        return None

class CreateCommand(Command):
    def __init__(self):
        super().__init__( "create")

    def parser(self):
        parser = argparse.ArgumentParser(prog='create', description="create a new instance")
        parser.add_argument(
            dest='name', nargs="?", help='Name of instance to create')
        parser.add_argument(
            '--password', dest="password", help='instance password, required if no pubkey avaiable')
        parser.add_argument(
            '--pubkey', dest="pubkey_path", help='pubkey path',default=f'{os.environ["HOME"]}/.ssh/id_rsa.pub')
        parser.add_argument(
            '--image', dest="image", default='docker-env-full:local', help='instance image. Must have SSH avaialble over port 22.')
        return parser


class InfoCommand(Command):
    def __init__(self):
        super().__init__( "info")

    def parser(self):
        parser = argparse.ArgumentParser(prog=self.name)
        parser.add_argument("instance", help='Instance name to get info for')
        return parser
        
class RestartCommand(Command):
    def __init__(self):
        super().__init__( "restart")

    def parser(self):
        parser = argparse.ArgumentParser(prog=self.name)
        parser.add_argument("instance", help='Instance name restart')
        return parser

class ConnectCommand(Command):
    def __init__(self):
        super().__init__( "connect")

    def parser(self):
        parser = argparse.ArgumentParser(prog=self.name)
        parser.add_argument("instance", help='Instance to connect to')
        return parser
        

class DisconnectCommand(Command):
    def __init__(self):
        super().__init__( "disconnect")

    def parser(self):
        parser = argparse.ArgumentParser(prog=self.name, description="disconnects tunnels from an instance")
        parser.add_argument("instance", help='Instance to disconnect')
        return parser
        

class SSHCommand(Command):
    def __init__(self):
        super().__init__( "ssh")

    def parser(self):
        parser = argparse.ArgumentParser(prog=self.name)
        parser.add_argument("instance", help='Instance to ssh to')
        return parser
        
class DestroyCommand(Command):
    def __init__(self):
        super().__init__( "destroy")

    def parser(self):
        parser = argparse.ArgumentParser(prog=self.name)
        parser.add_argument("instance", help='Instance to destroy')
        return parser
        