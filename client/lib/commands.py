
from abc import abstractmethod
import argparse
from dataclasses import dataclass
from multiprocessing.dummy import Array
import sys
import shlex
import os
from lib.client import DockerEnvClient



default_port=3001


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
        for c in self.commands:
            if c.handles(cmd):
                return c
        print(f'Unknown command {self.name}.{cmd}')




class RootCommand(Command):

    def __init__(self):
        super().__init__("root",[
            ListCommand(),
            HelpCommand(),
            CreateCommand(),
            ConnectCommand(),
            DestroyCommand(),
            QuitCommand(),
        ] )


    def parser(self):

        host=os.environ.get("HOST", "localhost")
        port=os.environ.get("PORT", default_port)

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
        print("Available commands: ls, create, destroy, connect")
        return None


class QuitCommand(Command):
    def __init__(self):
        super().__init__(["quit", "exit"])

    def parser(self):
        return None

    def command(self,name, args) -> 'CommandResult':
        print("")
        sys.exit(0)

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

class ConnectCommand(Command):
    def __init__(self):
        super().__init__( "connect")

    def parser(self):
        parser = argparse.ArgumentParser(prog=self.name)
        parser.add_argument("instance", help='Instance to connect to')
        return parser
        

class DestroyCommand(Command):
    def __init__(self):
        super().__init__( "destroy")

    def parser(self):
        parser = argparse.ArgumentParser(prog=self.name)
        parser.add_argument("instance", help='Instance to destroy')
        return parser
        