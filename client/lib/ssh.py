
import subprocess
import shlex
import sys
import re

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
        def __init__(self, proc: 'subprocess.Popen'):
            self.proc = proc
            self.stderr = ""
            self.stdout = ""

        def is_alive(self):
            return self.proc is not None and self.proc.poll() is None
        
        def output(self, streams='both') -> str:

            if self.proc is None:
                return ""

            # stdout, stderr = self.proc.communicate(timeout=1)

            # self.stdout += stdout
            # self.stderr += stderr

            # out = ""
            # if streams in ['both', 'stdout']:
            #     out = self.stdout
            
            # if streams in ['both', 'stderr']:
            #     out += self.stderr

            # return out
            return ""
        
        def kill(self):
            if self.is_alive():
                self.proc.kill()
                return True

            return False

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

        print(f'\tCommand: {command}')
        if MOCK:
            return SSH.SSHInstance(None)


        args = shlex.split(command)
        proc = subprocess.Popen(args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        proc.label = proc
        instance = SSH.SSHInstance(proc)

        if not instance.is_alive():
            print(f'Error: failed to tunnel exit code={instance.proc.returncode}')
            return None

        # output = instance.output()

        # if output.contains("known_hosts") or output.contains("fingerprint"):
        #     print(f'SSH needs fingerprint or known_hosts updates, please run this command, accept the prompts, then try again')
        #     print(f'\t{command}')
        #     instance.kill()
        #     return False

        return instance