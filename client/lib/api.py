from dataclasses import dataclass
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


headers_list = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

@dataclass
class APIResponse:
    status_code: int
    content: dict
    response: 'http.client.HTTPResponse'


class API:
    def __init__(self, container: 'Container', host, port, user):
        self.host = host
        self.port = port
        self.user = user
        self.printer = container.get(Printer)

    def _url(self, path):
        return f'/spaces/{self.user}{path}'

    def request(self, path, method='GET', payload=None, fatal=True) -> APIResponse:
        conn = http.client.HTTPConnection(self.host, self.port)

        try:
            url = self._url(path)
            body = None

            if payload:
                body = json.dumps(payload)
            conn.request(method, url, body=body, headers=headers_list)

            response = conn.getresponse()

            body = response.read()
            content = None


            if len(body) > 0:
                try:
                    content = json.loads(body)
                except json.JSONDecodeError:
                    self.printer.print(f'ERROR: not json: {body}')
                    content = {"error": body}

            return APIResponse(response.status, content, response)

        except ConnectionRefusedError:
            if fatal:
                self.printer.print(f'Cannot contact {self.host}:{self.port}, is it running?')
                sys.exit(1)
            return None
        finally:
            conn.close()




