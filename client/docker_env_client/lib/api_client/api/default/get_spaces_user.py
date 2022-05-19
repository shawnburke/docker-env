from typing import Any, Dict, List, Optional

import httpx

from ...client import Client
from ...models.instance import Instance
from ...types import Response


def _get_kwargs(
    user: str,
    *,
    client: Client,
) -> Dict[str, Any]:
    url = "{}/spaces/{user}".format(client.base_url, user=user)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[List[Instance]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = Instance.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[List[Instance]]:
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
) -> Response[List[Instance]]:
    """Get list of instances for user

    Args:
        user (str):

    Returns:
        Response[List[Instance]]
    """

    kwargs = _get_kwargs(
        user=user,
        client=client,
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
) -> Optional[List[Instance]]:
    """Get list of instances for user

    Args:
        user (str):

    Returns:
        Response[List[Instance]]
    """

    return sync_detailed(
        user=user,
        client=client,
    ).parsed


async def asyncio_detailed(
    user: str,
    *,
    client: Client,
) -> Response[List[Instance]]:
    """Get list of instances for user

    Args:
        user (str):

    Returns:
        Response[List[Instance]]
    """

    kwargs = _get_kwargs(
        user=user,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    user: str,
    *,
    client: Client,
) -> Optional[List[Instance]]:
    """Get list of instances for user

    Args:
        user (str):

    Returns:
        Response[List[Instance]]
    """

    return (
        await asyncio_detailed(
            user=user,
            client=client,
        )
    ).parsed
