from context import lib
from http.server import HTTPServer
import unittest
import time
from threading import Thread

class TestTunnel(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.container = lib.Container({
          lib.Printer: lib.NullPrinter(),
        })

    def test_events(self):

        server = HTTPServer(("localhost", 55999), lambda req, addr, server: 1)
        tunnel = lib.Tunnel(self.container,"Test", "localhost", 54321, 55999, expect_open=True)

        try:

            t = Thread(None, lambda: server.serve_forever(.1))
            t.start()
            time.sleep(1)
            result = tunnel.start()
            self.assertTrue(result)

        finally:
            server.server_close()
            server.shutdown()            
            tunnel.stop()

    def test_allocate_port(self):
        tunnel = lib.Tunnel(self.container,"Test", "localhost", 54321, None, expect_open=True)

        self.assertIsNone(tunnel.local_port)
        port = tunnel._ensure_local_port()
        self.assertNotEqual(port, 0)
        self.assertEqual(port, tunnel.local_port)
        self.assertFalse(lib.Tunnel.is_port_open(port))



if __name__ == '__main__':
    unittest.main()
