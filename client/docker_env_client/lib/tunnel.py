
from argparse import ArgumentError
from contextlib import closing
import socket
from enum import Enum
from .repeating_timer import RepeatingTimer
from .ssh import SSH
from .printer import Printer
from .container import Container


class TunnelEvents(Enum):
    CREATED = 1
    CONNECTED = 2
    DISCONNECTED = 3


class Tunnel:
    """
        Tunnel abstracts a connection to another box either directly
        or via SSH, and check for open port if it already exists.

        1. If the port is open already it will do nothing
        2. Otherwise, it will try to create an SSH tunnel
        3. If the tunnel fails, it will retry.
    """

    def __init__(self, container: 'Container', label, host, remote_port, local_port=None, message=None, ssh_port=None, user=None, expect_open=False):
        self.printer = container.get(Printer)
        self.container = container

        self.label = label
        self.host = host
        self.remote_port = remote_port
        if not remote_port:
            raise ArgumentError("remote_port", "remote port is required")
        self.local_port = local_port
        self.ssh_port = ssh_port
        self.message = message
        self.user = user

        self.timer = None
        self.connection = None
        self.port_status = None

        self.handlers = []
        self.add_handler(self._report_status)
        self.done = False
        self.expect_open = expect_open

    def add_handler(self, handler):
        """
            Handler is (label, Event)
        """
        self.handlers.append(handler)

    def remove_handler(self, handler):
        self.handlers.remove(handler)

    def _raise(self, event: 'TunnelEvents'):
        for handler in self.handlers:
            handler(self.label, event)

    @staticmethod
    def is_port_open(port) -> bool:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            return sock.connect_ex(("0.0.0.0", port)) == 0

    def _check_port_open(self) -> bool:
        return Tunnel.is_port_open(self.local_port)

    def _report_status(self, _, status):
        if self.done:
            return

        if status == TunnelEvents.CONNECTED:
            self.printer.print(
                f'Connected {self.label} as localhost:{self.local_port}')
            if self.message:
                self.printer.print(f'\t{self.status_message()}')
            return

        if status == TunnelEvents.DISCONNECTED:
            self.printer.print(
                f'Lost connection to {self.label} (localhost:{self.local_port}), will retry')

    def is_connected(self) -> bool:
        return self._check_connection()

    def start(self):
        self.done = False

        result = self._poll()

        if self.timer is None:
            self.timer = RepeatingTimer(5, self._poll, f'Tunnel {self.label}')
            self.timer.start()

        return result

    def stop(self):
        self.done = True
        if self.connection:
            self.connection.kill()
            self.connection = None
        self._check_connection() # to fire handlers

        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

    def status_message(self):
        message = "(Not connected)"
        if self.port_status:
            if self.message:
                message = self.message.replace(
                    "LOCAL_PORT", str(self.local_port))
            else:
                message = "(Connected)"
        return message

    def _poll(self):
        is_open = self._check_connection()
        if is_open or self.expect_open:
            return is_open

        if self._create_connection():
            return True

        self.printer.print(f'Failed to connect to {self.label}')
        return False

    def get_open_port(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

    def _ensure_local_port(self):
        if not self.local_port:
            self.local_port = SSH.find_existing(
                self.ssh_port, self.remote_port)

        if not self.local_port:
            self.local_port = self.get_open_port()

        return self.local_port

    def _create_connection(self):
        if not self.connection or not self.connection.is_alive():
            # if port is not open, try to start a tunnel
            ssh = self.container.create(SSH, self.container, self.host, self.ssh_port, self.user)
            self.connection = ssh.forward(self.remote_port, self.local_port)
            if not self.connection.ensure():
                self.printer.print(
                    f'Failed to set up connection to {self.label} on port {self.local_port}')
                return False

        return self._check_connection()

    def _check_connection(self):

        if not self._ensure_local_port():
            return False

        port_status = self.port_status
        result = self._check_port_open()

        if result != port_status:
            self.port_status = result
            if result:
                self._raise(TunnelEvents.CONNECTED)
            elif port_status:
                self._raise(TunnelEvents.DISCONNECTED)

        return result
