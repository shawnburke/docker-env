
from lib.repeating_timer import RepeatingTimer
from lib.tunnel import Tunnel
import socket

   
class Connection:
    def __init__(self, host, user, name, get_instance):
        self.user = user
        self.host = host
        self.name = name
        self.get_instance = get_instance
        self.tunnel = None
        self.ports = {}
        self.timer = RepeatingTimer(5, self._poll, f'Connection {name}')

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
            for t in self.ports.values():
                t.stop()
            self.ports = {}

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
        for port_info in instance.get("ports", []):
            remote_port = port_info["remote_port"]

            if 0 == self.forward_port(port_info["label"], remote_port, message=port_info.get("message"), check_ssh=False):
                print(f'Failed to start connection to {self.name} port {self.host}:{remote_port}')

        return True

    def tunnel_for_port(self, port) -> 'Tunnel':
        if port in self.ports:
            return self.ports[port]

        return "Unknown port"
    
    def forward_port(self, label, remote_port, local_port = 0, message=None, check_ssh=True) -> int:

        if remote_port in self.ports:
            return self.ports[remote_port].local_port

        if check_ssh and not self._poll():
            print(f'Unable to connect to {self.name} SSH port')
            return 0

        tunnel = self.ports.get(remote_port)
        if tunnel is None:
            tunnel = Tunnel(label, "localhost", remote_port=remote_port, local_port=0, message=message, ssh_port=self.tunnel.local_port, user=self.user)
            self.ports[remote_port] = tunnel
            
        if tunnel.start():
            return tunnel.local_port

        print(f'Unable to start tunnel to {self.name} {label} port={local_port}')
        return 0
