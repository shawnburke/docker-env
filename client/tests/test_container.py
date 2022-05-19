from docker_env_client import lib
import unittest


class TestContainer(unittest.TestCase):

    def test_create(self):
        c = lib.Container({
            lib.SSH: lib.SSH,
            lib.Printer: lib.NullPrinter(),
        })

        ssh = c.create(lib.SSH, c, "127.0.0.1", port=123)

        self.assertIsNotNone(ssh)
        self.assertEqual(ssh.port, 123)

    def test_get(self):

        c = lib.Container({
            lib.Printer: lib.Printer()
        })

        p = c.get(lib.Printer)
        self.assertIsNotNone(p)
        self.assertIsInstance(p, lib.Printer)


if __name__ == '__main__':
    unittest.main()