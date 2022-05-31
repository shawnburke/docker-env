from dis import get_instructions

import unittest
import mock
from os import path
import time

from docker_env_client import lib
from docker_env_client.lib.client import DockerEnvClient
from docker_env_client.lib.api_client.types import Response
from docker_env_client.lib.api_client.models import Instance, InstancePortsItem


class TestUser(unittest.TestCase):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config: lib.Config
        self.config = lib.Config()
        self.container = lib.Container({
          lib.Printer: lib.NullPrinter(),
          lib.Config: self.config
        })

    def setUp(self) -> None:
        self.conn = lib.Connection(self.container, "the-host", "the-user", "the-name", None)
        self.config.temp_dir_root = path.join("/tmp/fake/my-temp-dir", str(time.time_ns))
        return super().setUp()

    def test_portfile_path(self):
        val = self.conn._get_portfile_path(1234)
        self.assertEqual(path.join(self.config.temp_dir_root, "docker-env","the-user-the-name-1234.port"), val)

    def test_portfile_roundtrip(self):
        remote_port = time.time_ns() % 100000
        null_local_port = self.conn._get_local_port(remote_port)
        self.assertEqual(0, null_local_port)

        local_port = time.time_ns() % 1000

        self.conn._save_local_port(remote_port, local_port)

        cached_local_port = self.conn._get_local_port(remote_port)
        self.assertEqual(local_port, cached_local_port)

        # wipe out the cache
        self.conn.portmap = {}
        read_local_port = self.conn._get_local_port(remote_port)
        self.assertEqual(local_port, read_local_port)


    def test_poll(self):

        dead_tunnel = mock.Mock(name="dead_mock")
        dead_tunnel.stop.return_value = True
        self.conn.tunnels[9999] = dead_tunnel

        get_instance_mock = mock.Mock(name="get_instance_mock")
        get_instance_mock.return_value = Response['Instance'](
            200, None, {}, 
            Instance(
                name="footest",
                user="test-user", 
                status="happy",
                ssh_port="1022",
                ports=[
                    InstancePortsItem(label="Port A", message="PORT A on LOCAL_PORT", remote_port=1111),
                ],
            ))
        self.conn.get_instance = get_instance_mock

        ssh_tunnel_mock = mock.Mock(name="ssh_tunnel_mock")
        ssh_tunnel_mock.start.return_value = True
        ssh_tunnel_mock.add_handler.return_value = True
        

        port_mock = mock.Mock(name="port_mock")
        port_mock.start.return_value = True
        port_mock.local_port = 51111

        def creator(t, c, label, host, **kwargs):
            if label == "SSH":
                return ssh_tunnel_mock
            return port_mock

        self.container.create = creator
        
        self.conn._poll()

        ssh_tunnel_mock.start.assert_called_once()
        ssh_tunnel_mock.add_handler.assert_called_once()
        port_mock.start.assert_called_once()
        dead_tunnel.stop.assert_called_once()


        

if __name__ == '__main__':
    unittest.main()
