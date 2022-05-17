from typing import Any, Dict, Optional

import httpx

from ...client import Client
from ...models.instance import Instance
from ...types import Response


def _get_kwargs(
    user: str,
    name: str,
    *,
    client: Client,
) -> Dict[str, Any]:
    url = "{}/spaces/{user}/{name}".format(client.base_url, user=user, name=name)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[Instance]:
    if response.status_code == 200:
        response_200 = Instance.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[Instance]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    user: str,
    name: str,
    *,
    client: Client,
) -> Response[Instance]:
    """Get instance detail

    Args:
        user (str):
        name (str):

    Returns:
        Response[Instance]
    """

    kwargs = _get_kwargs(
        user=user,
        name=name,
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    user: str,
    name: str,
    *,
    client: Client,
) -> Optional[Instance]:
    """Get instance detail

    Args:
        user (str):
        name (str):

    Returns:
        Response[Instance]
    """

    return sync_detailed(
        user=user,
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    user: str,
    name: str,
    *,
    client: Client,
) -> Response[Instance]:
    """Get instance detail

    Args:
        user (str):
        name (str):

    Returns:
        Response[Instance]
    """

    kwargs = _get_kwargs(
        user=user,
        name=name,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    user: str,
    name: str,
    *,
    client: Client,
) -> Optional[Instance]:
    """Get instance detail

    Args:
        user (str):
        name (str):

    Returns:
        Response[Instance]
    """

    return (
        await asyncio_detailed(
            user=user,
            name=name,
            client=client,
        )
    ).parsed
