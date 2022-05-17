from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostSpacesUserJsonBody")


@attr.s(auto_attribs=True)
class PostSpacesUserJsonBody:
    """
    Attributes:
        user (Union[Unset, str]):
        name (Union[Unset, str]): Instance Name
        image (Union[Unset, str]):
        password (Union[Unset, str]):
        pubkey (Union[Unset, str]):
    """

    user: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    image: Union[Unset, str] = UNSET
    password: Union[Unset, str] = UNSET
    pubkey: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        user = self.user
        name = self.name
        image = self.image
        password = self.password
        pubkey = self.pubkey

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if user is not UNSET:
            field_dict["user"] = user
        if name is not UNSET:
            field_dict["name"] = name
        if image is not UNSET:
            field_dict["image"] = image
        if password is not UNSET:
            field_dict["password"] = password
        if pubkey is not UNSET:
            field_dict["pubkey"] = pubkey

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        user = d.pop("user", UNSET)

        name = d.pop("name", UNSET)

        image = d.pop("image", UNSET)

        password = d.pop("password", UNSET)

        pubkey = d.pop("pubkey", UNSET)

        post_spaces_user_json_body = cls(
            user=user,
            name=name,
            image=image,
            password=password,
            pubkey=pubkey,
        )

        post_spaces_user_json_body.additional_properties = d
        return post_spaces_user_json_body

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
