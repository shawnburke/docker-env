
from asyncio import InvalidStateError
import subprocess
import shlex
import sys
import re
from threading import local
import time
from .printer import Printer
from .container import Container
from .util import is_port_open

class SSH:
    """
        Abstracts SSH comms.

        Takes in parameters and formats an SSH command,
        then returns an SSHInstance which actually invokes the 
        command, etc.
    """
    def __init__(self, container: 'Container', host, port=None, user=None):
        self.printer = container.get(Printer)
        self.host = host
        self.port = port
        self.user = user

    @staticmethod
    def find_existing(ssh_port, remote_port):
        """
        find_existing looks for an existing ssh process that tunnels from local machine to the remote port.  
        this exists for clients that are started when tunnel is already running from another client instance.
        """
        proc = subprocess.run(["sh", "-c", f'pgrep -f -l ssh | grep {ssh_port} | grep ":{remote_port}"'],stdout=subprocess.PIPE)
        if proc.returncode != 0:
            return None
        
        m = re.search(r'(\d+):localhost:'+ str(remote_port), str(proc.stdout))
        if not m:
            return None

        return int(m.group(1))        
    class SSHInstance:
        """
            Abstracts an open SSH connection
        """
        def __init__(self, command: str, local_port=None):
            self.command = command
            self.proc = None
            self.stderr = ""
            self.stdout = ""
            self.local_port = local_port

        def is_alive(self):
            return self.proc is not None and self.proc.poll() is None

        def run(self, wait:float = .5, tries=10):
            if self.proc is not None:
                raise InvalidStateError()

            args = shlex.split(self.command)
            self.proc = subprocess.Popen(args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)

            
            for i in range(tries):
                time.sleep(wait)
                
                if not self.local_port:
                    return self.is_alive()

                if not self.is_alive():
                    return False
                
                if is_port_open(self.local_port):
                    return True


        def ensure(self):
            if self.proc is None:
                self.run()
   
            return self.is_alive()

        def kill(self):
            if self.is_alive():
                self.proc.kill()
                return True

            return False

        def wait(self):
            if not self.ensure():
                return

            self.proc.wait()

    def command(self, host=None, remote_port=None, local_port=None, forward_agent=False):
        args = ""
        if forward_agent:
            args = '-A'

        host = host or self.host or "localhost"

        if self.user is not None:
            host = f'{self.user}@{host}'
      
        if self.port is not None:
            args = f'-p {self.port} {args}'
        
        if local_port is None:

            if remote_port is None:
                return f'ssh {args} {host}'
            
            local_port = remote_port

        return  f'ssh {args} -NL {local_port}:localhost:{remote_port} {host}'


    def session(self):
        cmd = self.command(forward_agent=True)
        return SSH.SSHInstance(cmd)

    def forward(self, remote_port, local_port=None):
        """
            creates a port forward via SSH
        """
       
        cmd = self.command(self.host, remote_port, local_port)
        instance = SSH.SSHInstance(cmd, local_port=local_port)
        return instance