

from typing import List
from docker_env_client import lib
from docker_env_client.lib.client import DockerEnvClient
from docker_env_client.lib.api_client.types import Response
from docker_env_client.lib.api_client.models import Instance, InstancePortsItem
import unittest
import tempfile
from os import path
import mock
import os

class TestClient(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self) -> None:
        super().setUp()
        m = mock.Mock()
        p =  lib.NullPrinter()
        container = lib.Container({
          lib.Printer: p,
          lib.API: m,
        }, test_mode=True)

        c = DockerEnvClient(container, "test-usr", "1.2.3.4", 4321)
        self.client = c
        self.api_mock = m
        self.printer = p
        self.container = container
       
    def assertOutput(self, val):
        return self.printer.value.find(val)


    def _mock_get_instance(self, name="foo"):
        self.api_mock.get_instance.return_value = Response['Instance'](
            200, None, {}, 
            Instance(
                name=name,
                user="test-user", 
                status="happy",
                ssh_port="1022",
                ports=[
                    InstancePortsItem(label="Port A", message="PORT A on LOCAL_PORT", remote_port=1111),
                    InstancePortsItem(label="Port B", message="PORT B on LOCAL_PORT", remote_port=2222),
                ],
            ))
        
    def test_get(self):

      
        self._mock_get_instance()

        instance = self.client.get("foo")

        self.assertIsNotNone(instance)
        self.assertIsInstance(instance, Instance)
        self.assertOutput("Port A: 1111")
        self.assertOutput("Instance foo is happy")

    def test_list(self):

        
        self.api_mock.list_instances.return_value = Response[List['Instance']](
            200, None, {},
            [ 
                Instance(
                    name="foo",
                    user="test-user", 
                    status="happy",
                    ssh_port="1022",
                    ports=[
                        InstancePortsItem(label="Port A", message="PORT A on LOCAL_PORT", remote_port=1111),
                        InstancePortsItem(label="Port B", message="PORT B on LOCAL_PORT", remote_port=2222),
                    ],
                ),
                Instance(
                    name="bar",
                    user="test-user", 
                    status="sad",
                    ssh_port="1023",
                    ports=[
                        InstancePortsItem(label="Port A", message="PORT A on LOCAL_PORT", remote_port=1111),
                    ],
                )
            ])
       
        items = self.client.list()

        self.assertEqual(2, len(items))
        self.assertIsInstance(items[0], Instance)
        self.assertOutput("foo")
        self.assertOutput("bar")
        self.assertOutput("sad")

    def test_destroy_ok(self):
        
        self.api_mock.delete_instance.return_value = Response(
            200, None, {}, None)
        
        self.client.destroy("foo")
        self.assertOutput("Successfully deleted")

    def test_create(self):
        # c, m, p = self._create_client()

        self.api_mock.create_instance.return_value = Response['Instance'](
            201, None, {}, 
            Instance(
                name="baz",
                user="test-user", 
                status="happy",
                ssh_port=1022
            ))
        
        tf = path.join(tempfile.gettempdir(), "create-test.pub")

        try:
            with open(tf, "w") as pubfile:
                pubfile.write("some-rsa-stuff")

            instance = self.client.create(name="baz", password="password", pubkey_path=tf)
            self.assertIsNotNone(instance)
            self.assertEqual(instance.name, "baz")
            self.assertOutput("Created: baz")
        finally:
            os.remove(tf)

    def test_connect(self):
        connection_mock = mock.Mock()

        connection_mock.start.return_value = True

        self.container.register(lib.Connection, connection_mock)
        
        self._mock_get_instance()
      
        result = self.client.connect("foo")
        self.assertTrue(result)
        self.assertOutput("Successfully connected")

    def test_ssh(self):
        self._mock_get_instance()
        self.client._is_used = lambda port: True

        ssh_mock = mock.Mock()
        ssh_mock.wait.return_value = True

        session_mock = mock.Mock()
        session_mock.command = "ssh foo"
        ssh_mock.session.return_value = session_mock

        self.container.register(lib.SSH, ssh_mock)

        connection_mock = mock.Mock()
        connection_mock.create.return_value = mock.Mock()
        connection_mock.start.return_value = True
        
        self.container.register(lib.Connection, connection_mock)
        self.client.ssh("foo")
        self.assertOutput("Successfully connected")

if __name__ == '__main__':
    unittest.main()
