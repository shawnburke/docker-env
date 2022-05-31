from dataclasses import dataclass

from os import path
import tempfile

@dataclass
class Config:
    ssh_dir: str = path.expanduser("~/.ssh")
    check_interval_seconds: int = 5
    temp_dir_root: str = path.join(tempfile.gettempdir(), "_docker_env_client")