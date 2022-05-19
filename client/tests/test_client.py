

from docker_env_client import lib
from docker_env_client.lib.client import DockerEnvClient
from docker_env_client.lib.api_client.types import Response
from docker_env_client.lib.api_client.models import Instance, InstancePortsItem
import unittest
import mock

class TestClient(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
    def test_get(self):

        m = mock.Mock()

        m.get_instance.return_value = Response['Instance'](
            200, None, {}, 
            Instance(
                name="foo",
                user="test-user", 
                status="happy",
                ssh_port="1022",
                ports=[
                    InstancePortsItem(label="Port A", message="PORT A on LOCAL_PORT", remote_port=1111),
                    InstancePortsItem(label="Port B", message="PORT B on LOCAL_PORT", remote_port=2222),
                ],
            ))
        p =  lib.NullPrinter()
        container = lib.Container({
          lib.Printer: p,
          lib.API: m,
        }, test_mode=True)

        c = DockerEnvClient(container, "test-usr", "1.2.3.4", 4321)
        instance = c.get("foo")

        self.assertIsNotNone(instance)
        self.assertIsInstance(instance, Instance)
        self.assertTrue(p.value.find("Port A: 1111"))
        self.assertTrue(p.value.find("Instance foo is happy"))



if __name__ == '__main__':
    unittest.main()
