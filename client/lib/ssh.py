
from multiprocessing.sharedctypes import Value
import subprocess
import shlex
import sys
import re
import threading
from time import sleep

MOCK = False

class SSH:
    """
        Abstracts SSH comms
    """
    def __init__(self, host, port=None, user=None):
        self.host = host
        self.port = port
        self.user = user

    @staticmethod
    def find_existing(ssh_port, remote_port):
        proc = subprocess.run(["sh", "-c", f'pgrep -f -l ssh | grep {ssh_port} | grep ":{remote_port}"'],stdout=subprocess.PIPE)
        if proc.returncode != 0:
            return None
        
        m = re.search(f'(\d+):localhost:{remote_port}', str(proc.stdout))
        if not m:
            return None

        return int(m.group(1))        
        
    class SSHInstance:
        """
            Abstracts an open SSH connection
        """
        def __init__(self, proc: 'subprocess.Popen', host="localhost", ssh_port=22):
            self.proc = proc
            self.host = host
            self.ssh_port = ssh_port
            self.stderr_watcher = threading.Thread(target=self._watcher)
            self.stderr = proc.stderr
            self._done = False
            self.stderr_watcher.start()

        def is_alive(self):
            return self.proc is not None and self.proc.poll() is None
        
        def kill(self):

            self._done = True
            if self.proc:
                self.proc.terminate()
                self.proc = None
                return True

            return False

        def _on_err(self, err: str):
            err = err.lower()
            if err.find("connection refused"):
                print(f'Can not connect via ssh to {self.host}:{self.ssh_port}')


        def _watcher(self):
            while not self._done and self.is_alive():
                stderr = self.stderr.readline().decode()
                if len(stderr) > 0:
                    self._on_err(stderr)


        def wait(self):
            if not self.is_alive():
                return

            self.proc.wait()

    def command(self, host, remote_port, local_port=None, forward_agent=False):
        args="-NL"

        host = host or self.host or "localhost"

        if self.user is not None:
            host = f'{self.user}@{host}'
      
        if self.port is not None:
            args = f'-p {self.port} {args}'
        
        if forward_agent:
            args = f'-A {args}'

        if local_port is None:
            local_port = remote_port

        return  f'ssh {args} {local_port}:localhost:{remote_port} {host}'


    def forward(self, remote_port, local_port=None):
        """
            creates a port forward via SSH
        """
       
        command = self.command(self.host, remote_port, local_port)

        if MOCK:
            print(f'\tCommand: {command}')
            return SSH.SSHInstance(None)


        args = shlex.split(command)
        proc = None
        try:
            proc = subprocess.Popen(args, stdin=sys.stdin, stdout=sys.stdout, stderr=subprocess.PIPE)
        except ValueError:
            # we see this as a timing error when the tunnel fails and is shut down
            return None
        
        instance = SSH.SSHInstance(proc, self.host, self.port or 22)

        if not instance.is_alive():
            print(f'Error: failed to tunnel exit code={instance.proc.returncode}')
            return None

        return instance