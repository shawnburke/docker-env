import os
import http.client
import json
import sys
import socket

from lib.tunnel import Tunnel
from lib.connection import Connection
from lib.printer import Printer
from lib.container import Container
from lib.ssh import SSH

class DockerEnvClient(Printer):
    """
    this allows access to the docker env backend
    """
    def __init__(self, container: 'Container', user, host, port=3000):
        self.host = host
        self.port = port
        self.container = container
        self.container.register(Printer, self)
        self.hostport = f'{host}:{port}'
        self.user = user
        self.connections = {} # name => connection
        self.headers_list = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self._in_ssh = False

    def print(self, msg: str, end='\n'):
        if self._in_ssh:
            print("\n\r[ --- docker-env client --- ]")
            for line in msg.split('\n'):
                print(f'\r| {line}', end=end)
            print("\r[ --- ]\r\n")
        else:
            print("| " + msg)
        

    def _url(self, path):
        return f'/spaces/{self.user}{path}'

    def _request(self, path, method='GET', payload=None, fatal=True):
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
                    self.print(f'ERROR: not json: {body}')
                    content = {"error": body}

            return {
                "status": response.status,
                "content": content,
                "response": response
            }
        except ConnectionRefusedError:
            if fatal:
                self.print(f'Cannot contact {self.host}:{self.port}, is it running?')
                sys.exit(1)
            return False
        finally:
            conn.close()

    def init(self):
        self.api_tunnel = self.container.create(Tunnel, self.container, "API", self.host, 3001, self.port)
        return self.api_tunnel.start()

    def stop(self, code=0):
        for c in self.connections.values():
            c.stop()
        if self.api_tunnel:
            self.api_tunnel.stop()
        sys.exit(code)

    def create(self, name, password=None, pubkey_path=None, image=None):
        """
            Create an instance, with optional password and pubkey
        """
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
                self.print(f'Error: No pubkey found ({pubkey_path}), must supply password via "--password"')
                sys.exit(1)
        finally:
            # close file
            if pubkey_file:
                pubkey_file.close()

        response = self._request("", "POST", opts)
        status_code = response["status"]
        if status_code == 200 or status_code == 201:
            instance = response.get('content', {})
            self.print(f'Created {instance["name"]}')
            self.print(f'\tSSH Port: {instance["ssh_port"]}')
            self.print(f'Run `connect {instance["name"]}` to start tunnels')
        elif status_code == 409:
            self.print(f'Instance {name} already exists')
        else:
            self.print(f'Unexpected response {status_code}')

    def destroy(self, name):
        response = self._request(f'/{name}', "DELETE")
        status_code = response["status"]
        
        if status_code == 200:
            self.disconnect(name)
            self.print("Successfully deleted instance")
        elif status_code == 404:
            self.print(f'Unknown instance "{name}"')
        else:
            self.print(f'Unexpected response {status_code}')

    def _get_instance(self, name):
        response = self._request(f'/{name}')
        status_code = response["status"]
        instance = response["content"]

        if status_code == 200:
            return instance
        elif status_code == 404:
            return None
        
        self.print(f'Unexpected response {status_code}: {str(response)}')
        return None           
       

    def get(self, name):

        instance = self._get_instance(name)

        if instance is None:
            self.print("Can't find an instance of that name.")
            return None

        self.print(f'Instance {instance["name"]} is {instance["status"]}')
        self.print(f'\tSSH Port: {instance["ssh_port"]}')
        ports = instance.get("ports", [])

        c = None
        if name in self.connections:
            c = self.connections[name]
                
        if ports is not None:
            for p in ports:
                port = p.get("remote_port") 
                message = ""
                t = c and c.tunnel_for_port(port)
                if t:
                    message = f'{t.status_message()}'
                    port = t.local_port


                if message:
                    message = f'({message})'

                self.print(f'\t{p["label"]}: {port} {message}')
        self.print('')
        stats = instance.get('container_stats', None)
        if stats is not None:
            mem = stats["memory_stats"]["usage"]
            cpu = stats["cpu_stats"]["cpu_usage"]["total_usage"]
            self.print(f'\tMemory: {mem / (1024*1024)}mb')
            self.print(f'\tCPU: {cpu / 1000000000} cores (WIP! {cpu})')
            self.print('')
        if not c:
            self.print(f'Not connected, \'connect {name}\' to connect tunnels.')

    def list(self):
        response = self._request("")
        status_code =response["status"]
        if status_code == 200:
            instances = response["content"]
            if len(instances) == 0:
                self.print("No spaces active")
                return

            format_str = "{:15}{:15}{}"
            self.print(format_str.format("Name", "Status", "SSH Command"))
            self.print(format_str.format("----", "------", "-----------"))
            show_connected = False
            for instance in instances:
                ssh="not connected"
                status = instance["status"]
                name = instance["name"]
                if name in self.connections:
                    status = f'{status} (*)'
                    show_connected = True
                    ssh = f'ssh -p {instance["ssh_port"]} {instance["user"]}@localhost'
                
                self.print(format_str.format(name ,status, ssh))

            if show_connected:
                self.print("\n\t (*) Connected")
            return
        self.print(f'Unexpected status {response["status"]}')

    def _is_used(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(.1)                                 
            result = sock.connect_ex(('localhost',port))
            return result == 0
        finally:
            sock.close()

    def is_connected(self, name):
        return name in self.connections

    def connect(self, name):
        """
        connect sets up the SSH tunnel to the box, then sets up any 
        other ports
        """

        info = self._get_instance(name)
        if info is None:
            self.print(f'Can not find running instance {name}')
            return 
    
        host = info.get("host", self.host)
        
        connection = self.connections.get(name)
        
        if connection is None:
            connection = self.container.create(Connection, self.container, host, self.user, name, lambda name: self._request(f'/{name}'))
            self.connections[name] = connection

        if not connection.start():
            self.print(f'Instance {name} is not ready for connections (status=TK)')
            return

        self.print(f'Successfully connected to {name}')
        return True

    def disconnect(self, name):
        connection = self.connections.get(name)
        
        if connection is not None:
            connection.stop()
            del self.connections[name]
            self.print(f'Disconnected from {name}')
            return

        self.print(f'No connection exists for {name}')

    def forward(self, name, label, remote_port, local_port=None):
        connection = self.connections.get(name)
        if connection is None:
            self.connect(name)
            if name not in self.connections:
                self.print(f'Unable to connect to {name}')
        connection = self.connections.get(name)
        
        connection.forward_port(label, remote_port=remote_port, local_port=local_port)


    def ssh(self, name):

        instance = self._get_instance(name)
        if instance is None:
            self.print(f'Failed to get instance, does it exist?')
            return 

        if not self.is_connected(name) and not self.connect(name):
            self.print(f'Failed to connect to {name}')
            return

        ssh_port = instance["ssh_port"]

        if not self._is_used(ssh_port):
            self.print(f'SSH port is not open, run `docker-env connect {name}` first')
            return

        ssh = self.container.create(SSH, self, "localhost", ssh_port, self.user).session()
        self.print(ssh.command)
        try:
            self._in_ssh = True
            ssh.wait()
        finally:
            self._in_ssh = False
        


    def restart(self, name):
        instance = self._get_instance(name)

        if instance is None:
            self.print(f'Can\'t find instance {name}')
            return

        self.print('Restarting instance, this may take a bit...', end="")
        response = self._request(f'/{name}/restart', "POST")
        status_code = response["status"]
        if status_code == 200:
            self.print("done")
        else:
            self.print(f'failed: status={status_code}')

    
