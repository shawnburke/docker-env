
import socket
from lib.repeating_timer import RepeatingTimer
from contextlib import closing
from lib.ssh import SSH


class Tunnel:
    """
        Tunnel abstracts a connection to another box either directly
        or via SSH, and check for open port if it already exists.

        On disconnection it will attempt to reconnect
    """
    def __init__(self, label, host, remote_port, local_port, message = None, ssh_port=None, user=None):
        self.label = label
        self.host = host
        self.remote_port = remote_port
        self.local_port = local_port
        self.timer = None
        self.message = message
        self.connected = None
        self.connection = None
        self.ssh_port = ssh_port
        self.user = user
        

    def _check_port_open(self) -> bool:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            return sock.connect_ex(("0.0.0.0", self.local_port)) == 0

   
    def is_connected(self) -> bool:
        return self._check_connection()

    def start(self):
        result = self._poll()

        if self.timer is None:
            self.timer = RepeatingTimer(5, self._poll)
            self.timer.start()

        return result

    def stop(self):
        if self.connection:
            self.connection.kill()
            self.connection = None

        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        return None

    def _poll(self):
        success = self._check_connection()
        
        if success == self.connected:
            return success
        was_connected = self.connected
        self.connected = success
        if success:    
            print(f'Connected {self.label} as localhost:{self.local_port}')
            if self.message:
                print(f'\t{self.message.replace("LOCAL_PORT", str(self.local_port))}')
        
            return success

        if was_connected:
            print(f'Lost connection to {self.label} ({self.local_port}, will retry')
            return False
        
        print(f'Failed to connect to {self.label}')
        return False
      

    def _check_connection(self):

        
        # If port is open, do nothing
        if self._check_port_open():
            return True

        if self.connection is not None and self.connection.is_alive():
            return True
  
        # if port is not open, try to start a tunnel
        return self._setup_tunnel(self.label, self.remote_port, self.local_port, self.host, self.message)

    def _setup_tunnel(self, label, remote_port, local_port, jumpbox=None, message=""):
        
        ssh = SSH(jumpbox, self.ssh_port, self.user)

        self.connection = ssh.forward(remote_port, local_port, message)
        return self.connection.is_alive()

        