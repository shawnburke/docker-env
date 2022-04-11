import argparse

import os
import http.client
import json
import sys


class DockerEnvClient(object):
    """
    this allows access to the docker env backend
    """
    def __init__(self, args):
        self.host = args.host
        self.port = args.port
        self.hostport = f'{args.host}:{args.port}'
        self.user = os.environ["USER"]
        self.headers_list = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def _url(self, path):
        return f'/spaces/{self.user}{path}'

    def _request(self, path, method='GET', payload=None):
        conn = http.client.HTTPConnection(self.host, self.port)

        try:
            url = self._url(path)
            body = None

            if payload:
                body = json.dumps(payload)
            conn.request(method, url, body=body, headers=self.headers_list)

            response = conn.getresponse()

            body = response.read()
            content = None


            if len(body) > 0:
                try:
                    content = json.loads(body)
                except json.JSONDecodeError:
                    print(f'ERROR: not json: {body}')
                    content = {"error": body}

            return {
                "status": response.status,
                "content": content,
                "response": response
            }
        except ConnectionRefusedError:
            print(f'Cannot contact {self.host}:{self.port}, is it running?')
            sys.exit(1)
        finally:
            conn.close()

    def create(self, name, password=None, pubkey_path=None):
        opts = {
            "user": self.user,
            "name": name,
            "password": password,
        }

        
        # load the pubkey
        pubkey_file = None
        try:
            # read whole file to a string
            if pubkey_path == None:
                pubkey_path = "~/.ssh/id_rsa.pub"
            pubkey_file = open(pubkey_path, "r")
            opts["pubkey"] = pubkey_file.read()
        except FileNotFoundError:
            if password is None:
                print(f'Error: No pubkey found ({pubkey_path}), must supply password via "--password"')
                sys.exit(1)
        finally:
            # close file
            if pubkey_file:
                pubkey_file.close()

        response = self._request("", "POST", opts)
        status_code = response["status"]
        if status_code == 200 or status_code == 201:
            instance = response.get('content', {})
            print(f'Created {instance["name"]}')
            print(f'\tSSH Port: {instance["ssh_port"]}')
        elif status_code == 409:
            print(f'Instance {name} already exists')
        else:
            print(f'Unexpected response {status_code}')

    def destroy(self, name):
        response = self._request(f'/{name}', "DELETE")
        status_code = response["status"]
        
        if status_code == 200:
            print("Successfully deleted instance")
        elif status_code == 404:
            print(f'Unknown instance "{name}"')
        else:
            print(f'Unexpected response {status_code}')

    def get(self, name):

        response = self._request(f'/{name}')
        status_code = response["status"]
        instance = response["content"]

        if status_code == 200:
            print(f'Instance {instance["name"]} is {instance["status"]}')
            print(f'\tSSH Port: {instance["ssh_port"]}')
            print(f'\tVSCode Port: {instance["vscode_port"]}')
            print(f'')
            stats = instance.get('container_stats', {})
            mem = stats["memory_stats"]["usage"]
            print(f'\tMemory: {mem / (1024*1024)}mb')
            cpu = stats["cpu_stats"]["cpu_usage"]["total_usage"]
            print(f'\tCPU: {cpu / 1000000000} cores')

        elif status_code == 404:
            print("Can't find an instance of that name.")
        else:
            print(f'Unexpected response {status_code}')

    def list(self):
        response = self._request("")
        status_code =response["status"]
        if status_code == 200:
            instances = response["content"]
            if len(instances) == 0:
                print("No spaces active")
                return


            print('Name\t\tStatus')
            for instance in instances:
                
                print(f'{instance["name"]}\t\t{instance["status"]}')
            return
        print(f'Unexpected status {response.status}')

    def tunnel(self):
        print(
            f"ssh -A -p SSH_PORT -NL LOCAL_PORT:localhost:SSH_PORT {self.user}@localhost")

        response = self._request(f'/{name}')
        status_code = response["status"]
        if status_code != 200:
            print("Invalid instance name")
            return

        instance = response["content"]
        ssh_port = instance["ssh_port"]
        command = f'ssh -A -p {ssh_port} {ssh_port}:localhost:{ssh_port} {self.user}@localhost'
        print(command)        
        os.system(command)

    def ssh(self, name):

        response = self._request(f'/{name}')
        status_code = response["status"]
        if status_code != 200:
            print("Invalid instance name")
            return

        instance = response["content"]

        command = f'ssh -A -p {instance["ssh_port"]} {self.user}@localhost'
        print(command)        
        os.system(command)
        

if __name__ == '__main__':

    # create the top-level parser
    parser = argparse.ArgumentParser(prog='docker-env')
    parser.add_argument('--host', action='store', default="localhost",
                        help='docker_env host')
    parser.add_argument('--port', action='store', default=3001,
                        help='docker_env host')

    # create sub-parser
    sub_parsers = parser.add_subparsers(
        help='command help', dest="command_name")

    parser_create = sub_parsers.add_parser(
        'create', help='create new environment')
    parser_create.add_argument(
        dest='create_name', nargs='?', help='instance_name')
    parser_create.add_argument(
        '--password', dest="create_password", help='instance password, required if no pubkey avaiable')
    parser_create.add_argument(
        '--pubkey', dest="create_pubkey_path", help='pubkey path',default=f'{os.environ["HOME"]}/.ssh/id_rsa.pub')


    parser_ls = sub_parsers.add_parser(
        'ls', help='list current enviornments')

    parser_info = sub_parsers.add_parser(
        'info', help='list current enviornments')
    parser_info.add_argument(
        dest='info_name', nargs='?', help='instance_name')

    parser_destroy = sub_parsers.add_parser(
        'destroy', help='destroy an instance')
    parser_destroy.add_argument(
        dest='destroy_name', nargs='?', help='name to destroy')


    parser_ssh = sub_parsers.add_parser(
        'ssh', help='open a command prompt to the instance')
    parser_ssh.add_argument(dest='ssh_name', nargs='?', help='instance_name')

    parser_tunnel = sub_parsers.add_parser(
        'tunnel', help='list current enviornments')
    parser_tunnel.add_argument(dest='tunnel_name', nargs='?', help='instance name')


    args = parser.parse_args()

    cli = DockerEnvClient(args)

    if args.command_name == 'ls':
        cli.list()
    elif args.command_name == 'create':
        cli.create(args.create_name, args.create_password, args.create_pubkey_path)
    elif args.command_name == 'info':
        cli.get(args.info_name)
    elif args.command_name == 'destroy':
        cli.destroy(args.destroy_name)
    elif args.command_name == 'ssh':
        cli.ssh(args.ssh_name)
    elif args.command_name == 'tunnel':
        cli.ssh(args.tunnel_name)
