from typing import List

from .printer import Printer
from .container import Container

from .api_client import Client
from .api_client.api.default import get_spaces_user, get_spaces_user_name, get_health, post_spaces_user, post_spaces_user_name_restart, delete_spaces_user_name
from .api_client.models import Instance, GetHealthResponse200, PostSpacesUserJsonBody
from .api_client.types import Response

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
        return get_spaces_user_name.sync_detailed(user=user, name=name, client=self.api_client)
       
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

