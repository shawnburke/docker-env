
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



class Command:
    def __init__(self, name, commands = []):
        self.name = name
        self.commands = commands

    def exec(self, args) -> 'CommandResult':
        parser = self.parser()

        parsed = []

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
            HelpCommand()
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

    def command(self, args) -> 'CommandResult':
        print("Available commands: ls, create, destroy, connect")
        return None