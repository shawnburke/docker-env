
import argparse

import os
import http.client
import json
import sys
import socket
import subprocess
import time
import threading
from contextlib import closing


jumpboxFilePath="/tmp/.jumpbox"

class Tunnel:
    """
        Tunnel abstracts a connection to another box either directly
        or via SSH
    """
    def __init__(self, label, host, remote_port, local_port, message = None):
        self.label = label
        self.host = host
        self.remote_port = remote_port
        self.local_port = local_port
        self.timer = None
        self.message = message
        self.proc = None
        self.connected = None
        self.instance_timers = {}

    def _check_port_open(self) -> bool:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            return sock.connect_ex(("0.0.0.0", self.local_port)) == 0

    def start(self):
        result = self._poll()

        if self.timer is None:
            self.timer = threading.Timer(5, self._poll)
            self.timer.start()

        return result

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        return None

    def _poll(self):
        success = self._check_connection()
        
        if success == self.connected:
            return success

        self.connected = success
        if success:
            print(f'Connected {self.label} as localhost:{self.local_port}')
            if self.message:
                print(f'\tMessage: {self.message}')
            return success
        
        print(f'Failed to connect to {self.label}')
        return success
      

    def _check_connection(self):

        # If port is open, do nothing
        if self._check_port_open():
            return True

        if self.proc is not None and self.proc.poll():
            return True

        
        # if port is not open, try to start a tunnel
        return self._setup_tunnel(self.label, self.remote_port, self.local_port, self.host, self. message)

    def _setup_tunnel(self, label, remote_port, local_port, jumpbox=None, message=""):
        
        args="-NL"
        self.proc = subprocess.Popen(["ssh",args, f'{local_port}:localhost:{remote_port}', jumpbox])
        stdout, stderr = self.proc.communicate()
        if self.proc.poll() != None:
            print(f'Error: failed to tunnel exit code={self.proc.returncode}')
            return False
        
        if stdout.contains("known_hosts") or stdout.contains("fingerprint"):
            print(f'SSH needs fingerprint or known_hosts updates, please run this command, accept the prompts, then try again')
            print(f'\tssh {args} {local_port}:localhost:{local_port} {jumpbox}')
            return False

        print(f'Connected {label} as localhost:{local_port}')
        if message:
            print(f'\tMessage: {message}')
        # print(f'\tCommand: ssh {args} {local_port}:localhost:{local_port} {jumpbox}')
        self.proc.label = label
        return True

class DockerEnvClient(object):
    """
    this allows access to the docker env backend
    """
    def __init__(self, user, host, port=3000):
        self.host = host
        self.port = port
        self.hostport = f'{host}:{port}'
        self.user = user
        self.ports = {}
        self.headers_list = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

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
                    print(f'ERROR: not json: {body}')
                    content = {"error": body}

            return {
                "status": response.status,
                "content": content,
                "response": response
            }
        except ConnectionRefusedError:
            if fatal:
                print(f'Cannot contact {self.host}:{self.port}, is it running?')
                sys.exit(1)
            return False
        finally:
            conn.close()

    def init(self):
        
        api_tunnel = Tunnel("API", self.host, 3001, self.port)
        self.ports[self.port] = api_tunnel
        return api_tunnel.start()


       

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
            print(f'Run `docker-env connect {instance["name"]}` to start tunnels')
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
                    print(f'\t{p["label"]}: {p["port"]}')
            print('')
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


            print('Name\tStatus\tSSH')
            for instance in instances:
                ssh="n/a"
                if instance["status"] == "running":
                    ssh = f'ssh -p {instance["ssh_port"]} {instance["user"]}@localhost'
                print(f'{instance["name"]}\t{instance["status"]}\t{ssh}')
            return
        print(f'Unexpected status {response["status"]}')

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
                

    # def _setup_tunnel(self, label, remote_port, local_port, jumpbox=None, message=""):



    #     if jumpbox is None:
    #         jumpbox = self._load_jumpbox()
    #         if jumpbox:
    #             print(f'Loaded saved jumpbox {jumpbox}')

    #     if jumpbox is None:
    #         jumpbox = f'{self.user}@localhost'
        
    #     args="-NL"
    #     #if label == "SSH":
    #     #    args="-L"
    #     proc = subprocess.Popen(["ssh",args, f'{local_port}:localhost:{remote_port}', jumpbox])
    #     if proc.poll() != None:
    #         print(f'Error: failed to tunnel exit code={proc.returncode}')
    #         stdout, stderr = proc.communicate()
    #         return None
    #     else:
    #         print(f'Connected {label} as localhost:{local_port}')
    #         if message:
    #             print(f'\tMessage: {message}')
    #         print(f'\tCommand: ssh {args} {local_port}:localhost:{local_port} {jumpbox}')
    #         proc.label = label
    #     return proc


    # def _make_jumpbox_path(self):
    #     return f'{jumpboxFilePath}-{self.port}'

    # def _save_jumpbox(self, jumpbox):
    #     jb = open(self._make_jumpbox_path(), "w")
    #     jb.write(jumpbox)
    #     jb.close()
    #     print(f'Saved jumpbox {jumpbox}')
    
    # def _load_jumpbox(self):
    #     jb = None
    #     try:
    #         jb = open(self._make_jumpbox_path(), "r")
    #         return jb.read()
    #     except FileNotFoundError:
    #         return None
    #     finally:
    #         if jb:
    #           jb.close()

    def connect(self, name, jumpbox):
        """
        connect sets up the tunnel(s) to the box, mapping to local ports
        """


        if name == "api":
            # here we set up the basics for the api itself.
            tunnel = self._setup_tunnel("API", 3001, self.port, jumpbox)
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
            print('Failed to set up SSH tunnel.')
            sys.exit(1)

        tunnels.append(tunnel)

        ports = instance.get("ports", [])

        if ports is None:
            ports = []

        for p in ports:    
            offset += 1
            local_port = p["port"] # port_base + port.get("offset", offset)
            message = p.get("message", None)
            if message:
                message = message.replace("LOCAL_PORT", str(local_port))
            tunnel = self._setup_tunnel(p["label"], p["port"], local_port, jumpbox, message)
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
            print(f'SSH port is not open, run `docker-env connect {name}` first')
            sys.exit(1)

        command = f'ssh -A -p {ssh_port} {self.user}@localhost'
        print(command)        
        os.system(command)
        