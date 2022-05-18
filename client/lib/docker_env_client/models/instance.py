from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.instance_ports_item import InstancePortsItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="Instance")


@attr.s(auto_attribs=True)
class Instance:
    """
    Attributes:
        name (Union[Unset, str]):
        user (Union[Unset, str]):
        status (Union[Unset, str]):
        ssh_port (Union[Unset, int]):
        host (Union[Unset, str]):
        ports (Union[Unset, List[InstancePortsItem]]):
    """

    name: Union[Unset, str] = UNSET
    user: Union[Unset, str] = UNSET
    status: Union[Unset, str] = UNSET
    ssh_port: Union[Unset, int] = UNSET
    host: Union[Unset, str] = UNSET
    ports: Union[Unset, List[InstancePortsItem]] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        user = self.user
        status = self.status
        ssh_port = self.ssh_port
        host = self.host
        ports: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.ports, Unset):
            ports = []
            for ports_item_data in self.ports:
                ports_item = ports_item_data.to_dict()

                ports.append(ports_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if user is not UNSET:
            field_dict["user"] = user
        if status is not UNSET:
            field_dict["status"] = status
        if ssh_port is not UNSET:
            field_dict["ssh_port"] = ssh_port
        if host is not UNSET:
            field_dict["host"] = host
        if ports is not UNSET:
            field_dict["ports"] = ports

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name", UNSET)

        user = d.pop("user", UNSET)

        status = d.pop("status", UNSET)

        ssh_port = d.pop("ssh_port", UNSET)

        host = d.pop("host", UNSET)

        ports = []
        _ports = d.pop("ports", UNSET)
        for ports_item_data in _ports or []:
            ports_item = InstancePortsItem.from_dict(ports_item_data)

            ports.append(ports_item)

        instance = cls(
            name=name,
            user=user,
            status=status,
            ssh_port=ssh_port,
            host=host,
            ports=ports,
        )

        instance.additional_properties = d
        return instance

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
