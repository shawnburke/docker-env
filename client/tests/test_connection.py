from docker_env_client import lib
import unittest

class TestUser(unittest.TestCase):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.container = lib.Container({
          lib.Printer: lib.NullPrinter(),
        })

    def test_portfile_path(self):
        conn = lib.Connection(self.container, "the-host", "the-user", "the-name", None)
        val = conn._get_portfile_path(1234)
        self.assertEqual("/tmp/docker-env/the-user-the-name-1234.port", val)


if __name__ == '__main__':
    unittest.main()
