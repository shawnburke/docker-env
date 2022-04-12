import argparse

import os
import http.client
import json
import sys
import socket
import subprocess
import time

default_port=3001
jumpboxFilePath="/tmp/.jumpbox"

class DockerEnvClient(object):
    """
    this allows access to the docker env backend
    """
    def __init__(self, args):
        self.host = args.host
        self.port = args.port
        self.hostport = f'{args.host}:{args.port}'
        self.user = args.user
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

    def create(self, name, password=None, pubkey_path=None, image=None):
        opts = {
            "user": self.user,
            "name": name,
            "password": password,
        }

        if image:
            opts["image"] = image

        
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
            print(f'Run `docker-env connect [jumpbox]` to start tunnels')
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
            ports = instance.get("ports", [])
            if ports is not None:
                for p in ports:
                    print(f'\t{port["label"]}: {port["port"]}')
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

    def _is_used(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(.1)                                 
            result = sock.connect_ex(('localhost',port))
            return result == 0
        finally:
            sock.close()

    def _find_port_range(self):
        start = 50000

        while True:
            if not self._is_used(start+22):
                return start
                

    def _setup_tunnel(self, label, remote_port, local_port, jumpbox=None, message=""):



        if jumpbox is None:
            jumpbox = self._load_jumpbox()
            if jumpbox:
                print(f'Loaded saved jumpbox {jumpbox}')

        if jumpbox is None:
            jumpbox = f'{self.user}@localhost'
        
        args="-NL"
        #if label == "SSH":
        #    args="-L"
        proc = subprocess.Popen(["ssh",args, f'{local_port}:localhost:{remote_port}', jumpbox])
        if proc.poll() != None:
            print(f'Error: failed to tunnel exit code={proc.returncode}')
            stdout, stderr = proc.communicate()
            return None
        else:
            print(f'Connected {label} as localhost:{local_port}')
            if message:
                print(f'\tMessage: {message}')
            print(f'\tCommand: ssh {args} {local_port}:localhost:{local_port} {jumpbox}')
            proc.label = label
        return proc



    def _save_jumpbox(self, jumpbox):
        jb = open(jumpboxFilePath, "w")
        jb.write(jumpbox)
        jb.close()
        print(f'Saved jumpbox {jumpbox}')
    
    def _load_jumpbox(self):
        jb = None
        try:
            jb = open(jumpboxFilePath, "r")
            return jb.read()
        except FileNotFoundError:
            return None
        finally:
            if jb:
              jb.close()

    def connect(self, name, jumpbox):
        """
        connect sets up the tunnel(s) to the box, mapping to local ports
        """


        if name == "api":
            # here we set up the basics for the api itself.
            tunnel = self._setup_tunnel("API", self.port, 3001, jumpbox)
            if not tunnel.poll():
                # write a .jumpbox file
                self._save_jumpbox(jumpbox)
            return

        response = self._request(f'/{name}')
        status_code = response["status"]
        if status_code != 200:
            print("Invalid instance name")
            return

        instance = response["content"]
        ssh_port = instance["ssh_port"]

        # port_base = self._find_port_range()

        offset = 22
        tunnels = []
        tunnel = self._setup_tunnel("SSH", ssh_port, ssh_port, jumpbox)

        if tunnel is None:
            print(f'Failed to set up SSH tunnel.')
            sys.exit(1)

        tunnels.append(tunnel)

        ports = instance.get("ports", [])

        if ports is None:
            ports = []

        for port in ports:    
            offset += 1
            local_port = port["port"] # port_base + port.get("offset", offset)
            message = port.get("message", None)
            if message:
                message = message.replace("LOCAL_PORT", str(local_port))
            tunnel = self._setup_tunnel(port["label"], port["port"], local_port, jumpbox, message)
            if tunnel is not None:
                tunnels.append(tunnel)

        # every 1 second, poll the tunnels and exit if any have failed
        run = True
        while run:
            time.sleep(1)
            for tunnel in tunnels:
                status = tunnel.poll()
                if status is None:
                    continue

                print(f'Tunnel has exited: {tunnel.label}')
                run = False
                break
                
        # kill all tunnels
        for tunnel in tunnels:
            if tunnel.poll() is not None:
                tunnel.kill()

    def ssh(self, name):

        response = self._request(f'/{name}')
        status_code = response["status"]
        if status_code != 200:
            print("Invalid instance name")
            return

        instance = response["content"]

        ssh_port = instance["ssh_port"]

        if not self._is_used(ssh_port):
            print(f'SSH port is not open, run `docker-env connect {name} [jumpbox]` first')
            sys.exit(1)

        command = f'ssh -A -p {ssh_port} {self.user}@localhost'
        print(command)        
        os.system(command)
        

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

    # create sub-parser
    sub_parsers = parser.add_subparsers(
        help='command help', dest="command_name")

    #
    # CREATE Instance
    #
    parser_create = sub_parsers.add_parser(
        'create', help='create new instance')
    parser_create.add_argument(
        dest='create_name', nargs="?", help='Name of instance to create')
    parser_create.add_argument(
        '--password', dest="create_password", help='instance password, required if no pubkey avaiable')
    parser_create.add_argument(
        '--pubkey', dest="create_pubkey_path", help='pubkey path',default=f'{os.environ["HOME"]}/.ssh/id_rsa.pub')
    parser_create.add_argument(
        '--image', dest="create_image", help='instance image. Must have SSH avaialble over port 22.')
    
    
    #
    # List instances
    #

    parser_ls = sub_parsers.add_parser(
        'ls', help='list current instances')

    parser_info = sub_parsers.add_parser(
        'info', help='get instance detail')
    parser_info.add_argument(
        dest='info_name', nargs='?', help='name of instance')

    # 
    # destroy instance
    #
    parser_destroy = sub_parsers.add_parser(
        'destroy', help='destroy an instance')
    parser_destroy.add_argument(
        dest='destroy_name', nargs='?', help='name to instance to destroy')

    #
    # Connect via a jumpbox
    #
    parser_tunnel = sub_parsers.add_parser('connect', help='tunnel to instance jumpbox')
    parser_tunnel.add_argument(dest='tunnel_name', help='name of instance')
    parser_tunnel.add_argument(dest='tunnel_jumpbox', nargs="?", help='ssh target of jumpbox instance, e.g. somebox.foo.com or username@jumpbox.mycompany.com')

    #
    # SSH shell into instance
    #
    parser_ssh = sub_parsers.add_parser(
        'ssh', help='open a command prompt to the instance')
    parser_ssh.add_argument(dest='ssh_name', nargs='?', help='name of instance')



    args = parser.parse_args()

    cli = DockerEnvClient(args)

    if args.command_name == 'ls':
        cli.list()
    elif args.command_name == 'create':
        cli.create(args.create_name, password=args.create_password, pubkey_path=args.create_pubkey_path, image=args.create_image)
    elif args.command_name == 'info':
        cli.get(args.info_name)
    elif args.command_name == 'destroy':
        cli.destroy(args.destroy_name)
    elif args.command_name == 'ssh':
        cli.ssh(args.ssh_name)
    elif args.command_name == 'connect':
        cli.connect(args.tunnel_name, args.tunnel_jumpbox)
