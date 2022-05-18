from concurrent.futures import InvalidStateError
from dataclasses import dataclass
from typing import List

from lib.printer import Printer
from lib.container import Container

from lib.docker_env_client import Client
from lib.docker_env_client.api.default import get_spaces_user, get_spaces_user_name, get_health, post_spaces_user, post_spaces_user_name_restart, delete_spaces_user_name
from lib.docker_env_client.models import Instance, GetHealthResponse200, PostSpacesUserJsonBody
from lib.docker_env_client.types import Response

headers_list = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}




class API:
    def __init__(self, container: 'Container', host, port, user):
        self.host = host
        self.port = port
        self.user = user
        self.printer = container.get(Printer)
        self.api_client = Client(base_url=f'http://{host}:{port}', timeout=60)

    def get_instance(self, user, name) -> Response['Instance']:
        response = get_spaces_user_name.sync_detailed(user=user, name=name, client=self.api_client)
        if response.status_code == 200:
            return response
        return None

    def list_instances(self, user) -> Response[List['Instance']]:
        return get_spaces_user.sync_detailed(user=user, client=self.api_client)

    def get_health(self) -> 'GetHealthResponse200':
        return get_health.sync(client=self.api_client)
    
    def create_instance(self, user, name, pubkey=None, password=None, image=None) -> Response['Instance']:
        args = PostSpacesUserJsonBody(user=user, name=name, pubkey=pubkey,password=password,image=image)
        return post_spaces_user.sync_detailed(user=user, client=self.api_client, json_body=args)

    def restart_instance(self, user, name) -> Response:
        return post_spaces_user_name_restart.sync_detailed(user=user,name=name, client=self.api_client)

    def delete_instance(self, user, name) -> Response:
        return delete_spaces_user_name.sync_detailed(user=user,name=name, client=self.api_client)

