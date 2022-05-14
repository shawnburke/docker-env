import os
import tempfile
from os import path

from lib.repeating_timer import RepeatingTimer
from lib.tunnel import Tunnel
from lib.printer import Printer
from lib.container import Container

class Connection:
    def __init__(self, container: 'Container', host, user, name, get_instance):
        self.container = container
        self.printer = container.get(Printer)
        self.user = user
        self.host = host
        self.name = name
        self.get_instance = get_instance
        self.tunnel = None
        self.tunnels = {}
        self.portmap = {}
        self.timer = None

    def start(self):

        if self.is_alive():
            return True

        if self.timer is None:
            self.timer = RepeatingTimer(5, self._poll, f'Connection {self.name}')

        result = self._poll()
        if result:
            self.timer.start()
        return result


    def stop(self):
        if self.is_alive():
            self.timer.cancel()
            self.tunnel.stop()
            for t in self.tunnels.values():
                t.stop()
            self.tunnels = {}

    def is_alive(self) -> bool:
        return self.tunnel and self.tunnel.is_connected()

    def _get_portfile_path(self, remote_port) -> str:
        # if it's zero, look on disk
        tmpdir = path.join(tempfile.gettempdir(), "docker-env")
        try:
            os.mkdir(tmpdir)
        except FileExistsError:
            # do nothing
            pass

        return path.join(tmpdir, f'{self.user}-{self.name}-{remote_port}.port')

    def _get_local_port(self, remote_port):
        # portmap is a file like [instance].[user].remote_port_.port, with contents being the local port
        local_port = self.portmap.get(remote_port, 0)

        if local_port != 0:
            return local_port

        portfile_path = self._get_portfile_path(remote_port)
        if not path.exists(portfile_path):
            return 0

        with open(portfile_path, "r") as portfile:
            try:
                port = int(portfile.read())
                self.portmap[remote_port] = port
                return port
            except ValueError as ex:
                self.printer.print(f'Error reading portfile {portfile_path}: {ex}')
                pass

        return 0

    def _save_local_port(self, remote_port, local_port):

        self.portmap[remote_port] = local_port
        portfile_path = self._get_portfile_path(remote_port)
        with open(portfile_path, "w") as portfile:
            portfile.write(str(local_port))



    def _poll(self) -> bool:
            # check the instance
        response = self.get_instance(self.name)
        status_code = response["status"]
        if status_code != 200:
            self.printer.print("Invalid instance name")
            return False

        instance = response["content"]
        ssh_port = instance["ssh_port"]

        if not self.is_alive():
            if self.tunnel:
                self.tunnel.stop()

            self.tunnel = Tunnel(self.container, "SSH", self.host, ssh_port, ssh_port, f'Connected to SSH for {self.name}')
            if not self.tunnel.start():
                return False

        # walk the other ports
        seen = {}
        for port_info in instance.get("ports", []):
            remote_port = port_info["remote_port"]
            seen[remote_port] = True

            if remote_port in self.tunnels:
                continue

            local_port = self.forward_port(
                port_info["label"], 
                remote_port,
                local_port= self._get_local_port(remote_port),
                message=port_info.get("message"), 
                check_ssh=False)

            if 0 == local_port:
                self.printer.print(f'Failed to start connection to {self.name} port {self.host}:{remote_port}')
                continue

            self._save_local_port(remote_port, local_port)

        # check for closed ports
        keys = list(self.tunnels.keys())
        for remote_port in keys:
            if remote_port in seen:
                continue
            tunnel = self.tunnels[remote_port]

            self.printer.print(f'Closing tunnel to port {tunnel.local_port} (Remote port {remote_port}) as it seems to be no longer open.')
            tunnel.stop()
            del self.tunnels[remote_port]

        return True

    def tunnel_for_port(self, port) -> 'Tunnel':
        if port in self.tunnels:
            return self.tunnels[port]

        return None

    def forward_port(self, label, remote_port, local_port = 0, message=None, check_ssh=True) -> int:
        tunnel = self.tunnels.get(remote_port, None)
        if tunnel is not None:
            return self.tunnels[remote_port].local_port

        if check_ssh and not self._poll():
            self.printer.print(f'Unable to connect to {self.name} SSH port')
            return 0

        tunnel = self.container.create(Tunnel, self.container, label, "localhost", remote_port=remote_port, local_port=local_port, message=message, ssh_port=self.tunnel.local_port, user=self.user)
        self.tunnels[remote_port] = tunnel

        if tunnel.start():
            return tunnel.local_port

        self.printer.print(f'Unable to start tunnel to {self.name} {label} port={local_port}')
        return 0
