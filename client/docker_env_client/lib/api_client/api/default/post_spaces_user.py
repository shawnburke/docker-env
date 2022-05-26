from typing import Any, Dict, Optional, Union, cast

import httpx

from ...client import Client
from ...models.instance import Instance
from ...models.post_spaces_user_json_body import PostSpacesUserJsonBody
from ...models.post_spaces_user_response_400 import PostSpacesUserResponse400
from ...types import Response


def _get_kwargs(
    user: str,
    *,
    client: Client,
    json_body: PostSpacesUserJsonBody,
) -> Dict[str, Any]:
    url = "{}/spaces/{user}".format(client.base_url, user=user)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[Union[Any, Instance, PostSpacesUserResponse400]]:
    if response.status_code == 201:
        response_201 = Instance.from_dict(response.json())

        return response_201
    if response.status_code == 400:
        response_400 = PostSpacesUserResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 409:
        response_409 = cast(Any, None)
        return response_409
    return None


def _build_response(*, response: httpx.Response) -> Response[Union[Any, Instance, PostSpacesUserResponse400]]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    user: str,
    *,
    client: Client,
    json_body: PostSpacesUserJsonBody,
) -> Response[Union[Any, Instance, PostSpacesUserResponse400]]:
    """Create a new instance

    Args:
        user (str):
        json_body (PostSpacesUserJsonBody):

    Returns:
        Response[Union[Any, Instance, PostSpacesUserResponse400]]
    """

    kwargs = _get_kwargs(
        user=user,
        client=client,
        json_body=json_body,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    user: str,
    *,
    client: Client,
    json_body: PostSpacesUserJsonBody,
) -> Optional[Union[Any, Instance, PostSpacesUserResponse400]]:
    """Create a new instance

    Args:
        user (str):
        json_body (PostSpacesUserJsonBody):

    Returns:
        Response[Union[Any, Instance, PostSpacesUserResponse400]]
    """

    return sync_detailed(
        user=user,
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    user: str,
    *,
    client: Client,
    json_body: PostSpacesUserJsonBody,
) -> Response[Union[Any, Instance, PostSpacesUserResponse400]]:
    """Create a new instance

    Args:
        user (str):
        json_body (PostSpacesUserJsonBody):

    Returns:
        Response[Union[Any, Instance, PostSpacesUserResponse400]]
    """

    kwargs = _get_kwargs(
        user=user,
        client=client,
        json_body=json_body,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    user: str,
    *,
    client: Client,
    json_body: PostSpacesUserJsonBody,
) -> Optional[Union[Any, Instance, PostSpacesUserResponse400]]:
    """Create a new instance

    Args:
        user (str):
        json_body (PostSpacesUserJsonBody):

    Returns:
        Response[Union[Any, Instance, PostSpacesUserResponse400]]
    """

    return (
        await asyncio_detailed(
            user=user,
            client=client,
            json_body=json_body,
        )
    ).parsed
