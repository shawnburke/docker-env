
from argparse import ArgumentError
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
        if not remote_port:
            raise ArgumentError("remote_port")
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
            self.timer = RepeatingTimer(5, self._poll, f'Tunnel {self.label}')
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

    def status_message(self):
        message = "(Not connected)"
        if self.connected:
            if self.message:
                message = self.message.replace("LOCAL_PORT", str(self.local_port))
            else:
                message = "(Connected)"
        return message


    def _poll(self):
        success = self._check_connection()
        
        if success == self.connected:
            return success
        was_connected = self.connected
        self.connected = success
        if success:    
            print(f'Connected {self.label} as localhost:{self.local_port}')
            if self.message:
                print(f'\t{self.status_message()}')
        
            return success

        if was_connected:
            print(f'Lost connection to {self.label} ({self.local_port}, will retry')
            return False
        
        print(f'Failed to connect to {self.label}')
        return False
      
    
    def get_open_port(self):
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

    def _ensure_local_port(self):
        if not self.local_port:
            self.local_port = SSH.find_existing(self.ssh_port, self.remote_port)

        if not self.local_port:
            self.local_port = self.get_open_port()

        return self.local_port

    def _check_connection(self):

        if not self._ensure_local_port():
            return False 
            
        
        # If port is open, do nothing
        if self._check_port_open():
            return True

        if self.connection is not None and self.connection.is_alive():
            return True
  
        # if port is not open, try to start a tunnel
        ssh = SSH(self.host, self.ssh_port, self.user)
        self.connection = ssh.forward(self.remote_port, self.local_port)
        return self.connection.is_alive()

        