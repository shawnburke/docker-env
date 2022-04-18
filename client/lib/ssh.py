
import subprocess

MOCK = True

class SSH:
    """
        Abstracts SSH comms
    """
    def __init__(self, host, port=None, user=None):
        self.host = host
        self.port = port
        self.user = user


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

            stdout, stderr = self.proc.communicate();

            self.stdout += stdout
            self.stderr += stderr

            out = ""
            if streams in ['both', 'stdout']:
                out = self.stdout
            
            if streams in ['both', 'stderr']:
                out += self.stderr

            return out
        
        def kill(self):
            if self.is_alive():
                self.proc.kill()
                return True

            return False

        def wait(self):
            if not self.is_alive():
                return

            self.proc.wait()


    def forward(self, remote_port, local_port=None, message=None):
        """
            creates a port forward via SSH
        """
        args="-NL"

        host = self.host
        if host is None:
            host = "localhost"

        if self.user is not None:
            host = f'{self.user}@{host}'
      
        if self.port is not None:
            args = f'{args} -p {self.port}'

        if MOCK:
            print(f'\tCommand: ssh {args} {local_port}:localhost:{local_port} {host}')
            return SSH.SSHInstance(None)



        proc = subprocess.Popen(["ssh",args, f'{local_port}:localhost:{remote_port}', host])
        proc.label = proc
        instance = SSH.SSHInstance(proc)

        if not instance.is_alive():
            print(f'Error: failed to tunnel exit code={instance.proc.returncode}')
            return False

        output = instance.output()

        if output.contains("known_hosts") or output.contains("fingerprint"):
            print(f'SSH needs fingerprint or known_hosts updates, please run this command, accept the prompts, then try again')
            print(f'\tssh {args} {local_port}:localhost:{local_port} {jumpbox}')
            instance.kill()
            return False

        print(f'Connected {label} as localhost:{local_port}')
        if message:
            print(f'\tMessage: {message}')
        
        return True