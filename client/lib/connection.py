
from lib.repeating_timer import RepeatingTimer
from lib.tunnel import Tunnel

   
class Connection:
    def __init__(self, host, user, name, get_instance):
        self.user = user
        self.host = host
        self.name = name
        self.get_instance = get_instance
        self.tunnel = None
        self.ports = {}
        self.timer = RepeatingTimer(5, self._poll)

    def start(self):
        if self.is_alive():
            return True
        result = self._poll()
        if result:
            self.timer.start()
        return result


    def stop(self):
        if self.is_alive():
            self.timer.cancel()
            self.tunnel.stop()
            for _, t in self.ports:
                t.stop()

    def is_alive(self) -> bool:
        return self.tunnel and self.tunnel.is_connected()


    def _poll(self) -> bool:
            # check the instance
        response = self.get_instance(self.name)
        status_code = response["status"]
        if status_code != 200:
            print("Invalid instance name")
            return False

        instance = response["content"]
        ssh_port = instance["ssh_port"]

        if not self.is_alive():
            if self.tunnel:
                self.tunnel.stop()

            self.tunnel = Tunnel("SSH", self.host, ssh_port, ssh_port, f'Connected to SSH for {self.name}')
            if not self.tunnel.start():
                return False

        # walk the other ports
        for portInfo in instance.get("ports", []):
            port = portInfo["port"]

            if 0 == self.forward_port(portInfo["label"], port, portInfo.get("message"), False):
                print(f'Failed to start connection to {self.name} port {port}')

        return True

    def forward_port(self, label, port, message=None, check_ssh=True) -> int:

        if port in self.ports:
            return port

        if check_ssh and not self._poll():
            print(f'Unable to connect to {self.name} SSH port')
            return 0

        tunnel = self.ports.get(port)
        if tunnel is None:
            tunnel = Tunnel(label, "localhost", port, port, message, ssh_port=self.tunnel.local_port, user=self.user)

        if tunnel.start():
            return port

        print(f'Unable to start tunnel to {self.name} {label} port={port}')
        return 0
