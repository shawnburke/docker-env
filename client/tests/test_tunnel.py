from context import lib
from http.server import HTTPServer
import unittest
import time
from threading import Thread

class TestTunnel(unittest.TestCase):

    def test_events(self):

        server = HTTPServer(("localhost", 55999), lambda req, addr, server: 1)
        tunnel = lib.Tunnel(None,"Test", "localhost", 54321, 55999, expect_open=True)

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


if __name__ == '__main__':
    unittest.main()
