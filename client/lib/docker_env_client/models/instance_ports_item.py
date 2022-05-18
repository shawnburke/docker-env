from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="InstancePortsItem")


@attr.s(auto_attribs=True)
class InstancePortsItem:
    """
    Attributes:
        label (Union[Unset, str]):
        message (Union[Unset, str]):
        port (Union[Unset, int]):
        remote_port (Union[Unset, int]):
    """

    label: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET
    port: Union[Unset, int] = UNSET
    remote_port: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        label = self.label
        message = self.message
        port = self.port
        remote_port = self.remote_port

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if label is not UNSET:
            field_dict["label"] = label
        if message is not UNSET:
            field_dict["message"] = message
        if port is not UNSET:
            field_dict["port"] = port
        if remote_port is not UNSET:
            field_dict["remote_port"] = remote_port

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        label = d.pop("label", UNSET)

        message = d.pop("message", UNSET)

        port = d.pop("port", UNSET)

        remote_port = d.pop("remote_port", UNSET)

        instance_ports_item = cls(
            label=label,
            message=message,
            port=port,
            remote_port=remote_port,
        )

        instance_ports_item.additional_properties = d
        return instance_ports_item

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
