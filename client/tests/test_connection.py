from context import lib
import unittest

class TestUser(unittest.TestCase):

    def test_user_activation(self):
        conn = lib.Connection(None, "the-host", "the-user", "the-name", None)
        val = conn._get_portfile_path(1234)
        self.assertEqual("/tmp/docker-env/the-user-the-name-1234.port", val)


if __name__ == '__main__':
    unittest.main()
