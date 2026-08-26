from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.async_api_client import AsyncAPIClient


@pytest.mark.anyio
async def test_async_api_client_post():
    mock_response = MagicMock()

    mock_response.url = "https://example.com/api"

    mock_response.json.return_value = {
        "success": True,
        "message": "Hello",
    }

    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()

    mock_client.post = AsyncMock(
        return_value=mock_response
    )

    mock_context = MagicMock()

    mock_context.__aenter__ = AsyncMock(
        return_value=mock_client
    )

    mock_context.__aexit__ = AsyncMock(
        return_value=None
    )

    with patch(
        "src.async_api_client.httpx.AsyncClient",
        return_value=mock_context,
    ):
        client = AsyncAPIClient()

        response = await client.post(
            "https://example.com/api",
            {
                "name": "Sebastian",
            },
        )

    assert response.url == "https://example.com/api"
    assert response.data["success"] is True
    assert response.data["message"] == "Hello"

    mock_client.post.assert_awaited_once()


@pytest.mark.anyio
async def test_async_api_client_retries_after_request_error():
    mock_response = MagicMock()

    mock_response.url = "https://example.com/api"

    mock_response.json.return_value = {
        "success": True,
    }

    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()

    mock_client.post = AsyncMock(
        side_effect=[
            httpx.RequestError("Connection failed"),
            httpx.RequestError("Connection failed"),
            mock_response,
        ]
    )

    mock_context = MagicMock()

    mock_context.__aenter__ = AsyncMock(
        return_value=mock_client
    )

    mock_context.__aexit__ = AsyncMock(
        return_value=None
    )

    with patch(
        "src.async_api_client.httpx.AsyncClient",
        return_value=mock_context,
    ), patch(
        "src.async_api_client.asyncio.sleep",
        new_callable=AsyncMock,
    ) as mock_sleep:

        client = AsyncAPIClient(
            max_retries=3
        )

        response = await client.post(
            "https://example.com/api",
            {
                "name": "Sebastian",
            },
        )

    assert response.data["success"] is True
    assert mock_client.post.await_count == 3
    assert mock_sleep.await_count == 2

    mock_sleep.assert_any_await(1)
    mock_sleep.assert_any_await(2)


@pytest.mark.anyio
async def test_async_api_client_retries_on_503():
    failed_response = MagicMock()

    failed_response.status_code = 503
    failed_response.headers = {}

    successful_response = MagicMock()

    successful_response.status_code = 200
    successful_response.url = "https://example.com/api"

    successful_response.json.return_value = {
        "success": True,
    }

    successful_response.raise_for_status.return_value = None

    mock_client = MagicMock()

    mock_client.post = AsyncMock(
        side_effect=[
            failed_response,
            failed_response,
            successful_response,
        ]
    )

    mock_context = MagicMock()

    mock_context.__aenter__ = AsyncMock(
        return_value=mock_client
    )

    mock_context.__aexit__ = AsyncMock(
        return_value=None
    )

    with patch(
        "src.async_api_client.httpx.AsyncClient",
        return_value=mock_context,
    ), patch(
        "src.async_api_client.asyncio.sleep",
        new_callable=AsyncMock,
    ) as mock_sleep:

        client = AsyncAPIClient(
            max_retries=3
        )

        response = await client.post(
            "https://example.com/api",
            {
                "name": "Sebastian",
            },
        )

    assert response.data["success"] is True

    assert mock_client.post.await_count == 3
    assert mock_sleep.await_count == 2

    mock_sleep.assert_any_await(1)
    mock_sleep.assert_any_await(2)

@pytest.mark.anyio
async def test_async_api_client_respects_retry_after():
    rate_limited_response = MagicMock()

    rate_limited_response.status_code = 429

    rate_limited_response.headers = {
        "Retry-After": "5"
    }

    successful_response = MagicMock()

    successful_response.status_code = 200
    successful_response.url = "https://example.com/api"

    successful_response.json.return_value = {
        "success": True,
    }

    successful_response.raise_for_status.return_value = None

    mock_client = MagicMock()

    mock_client.post = AsyncMock(
        side_effect=[
            rate_limited_response,
            successful_response,
        ]
    )

    mock_context = MagicMock()

    mock_context.__aenter__ = AsyncMock(
        return_value=mock_client
    )

    mock_context.__aexit__ = AsyncMock(
        return_value=None
    )

    with patch(
        "src.async_api_client.httpx.AsyncClient",
        return_value=mock_context,
    ), patch(
        "src.async_api_client.asyncio.sleep",
        new_callable=AsyncMock,
    ) as mock_sleep:

        client = AsyncAPIClient(
            max_retries=3
        )

        response = await client.post(
            "https://example.com/api",
            {
                "name": "Sebastian",
            },
        )

    assert response.data["success"] is True

    assert mock_client.post.await_count == 2

    mock_sleep.assert_awaited_once_with(5)    