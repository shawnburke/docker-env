from docker_env_client import lib
import unittest


class TestSSH(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.container = lib.Container({
          lib.Printer: lib.NullPrinter(),
        })

    def test_forward(self):

        ssh = lib.SSH(self.container, "localhost", 55022, "test-user")
        instance = ssh.forward(55000, 55001)
        self.assertEqual(instance.command, "ssh -p 55022  -NL 55001:localhost:55000 test-user@localhost")


    def test_session(self):

        ssh = lib.SSH(self.container, "127.0.0.1", 55022, "test-user")
        instance = ssh.session()
        self.assertEqual(instance.command, "ssh -p 55022 -A test-user@127.0.0.1")


if __name__ == '__main__':
    unittest.main()
