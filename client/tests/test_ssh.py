from context import lib
import unittest


class TestTunnel(unittest.TestCase):

    def test_ssh(self):

        ssh = lib.SSH(lib.NullPrinter(), "localhost", 55022, "test-user")
        instance = ssh.forward(55000, 55001)
        self.assertEqual(instance.command, "ssh -p 55022  -NL 55001:localhost:55000 test-user@localhost")


    def test_forward(self):

        ssh = lib.SSH(lib.NullPrinter(), "localhost", 55022, "test-user")
        command = ssh.command("localhost", None, None, True)
        self.assertEqual(command, "ssh -p 55022 -A test-user@localhost")


if __name__ == '__main__':
    unittest.main()
