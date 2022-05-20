

from contextlib import closing
import socket

def is_port_open(port) -> bool:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex(("0.0.0.0", port)) == 0