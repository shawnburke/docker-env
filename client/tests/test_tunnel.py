from docker_env_client import lib
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

        sc = False
        sd = False

        def handler(label, event):
            nonlocal sc
            nonlocal sd
            sc = sc or event == lib.TunnelEvents.CONNECTED
            sd = sd or event == lib.TunnelEvents.DISCONNECTED

        try:
            tunnel.add_handler(handler)
            t = Thread(None, lambda: server.serve_forever(.1))
            t.start()
            time.sleep(1)
            result = tunnel.start()
            self.assertTrue(result)

            self.assertTrue(sc)
    
        finally:
            server.server_close()
            server.shutdown()
            tunnel._poll()
            self.assertTrue(sd)  
            tunnel.stop()

    def test_allocate_port(self):
        tunnel = lib.Tunnel(self.container,"Test", "localhost", 54321, None, expect_open=True)

        self.assertIsNone(tunnel.local_port)
        port = tunnel._ensure_local_port()
        self.assertNotEqual(port, 0)
        self.assertEqual(port, tunnel.local_port)
        self.assertFalse(lib.util.is_port_open(port))

if __name__ == '__main__':
    unittest.main()
