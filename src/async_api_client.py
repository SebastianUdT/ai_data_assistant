import asyncio
from typing import Any

import httpx
from pydantic import BaseModel

from src.config import settings


RETRYABLE_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}


class APIResponse(BaseModel):
    url: str
    data: dict[str, Any]


class AsyncAPIClient:
    def __init__(
        self,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.timeout = (
            timeout
            if timeout is not None
            else settings.api_timeout
        )

        self.max_retries = (
            max_retries
            if max_retries is not None
            else settings.max_retries
        )

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.api_key}",
        }

    def _get_retry_delay(
        self,
        response: httpx.Response,
        attempt: int,
    ) -> float:
        retry_after = response.headers.get(
            "Retry-After"
        )

        if isinstance(retry_after, str):
            try:
                return float(retry_after)
            except ValueError:
                pass

        return 2 ** attempt

    async def post(
        self,
        url: str,
        data: dict[str, Any],
    ) -> APIResponse:

        headers = self._get_headers()

        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:

            for attempt in range(
                self.max_retries + 1
            ):
                try:
                    response = await client.post(
                        url,
                        json=data,
                        headers=headers,
                    )

                    if (
                        response.status_code
                        in RETRYABLE_STATUS_CODES
                    ):
                        if attempt == self.max_retries:
                            response.raise_for_status()

                        delay = self._get_retry_delay(
                            response,
                            attempt,
                        )

                        print(
                            f"HTTP {response.status_code}. "
                            f"Retrying in {delay} seconds..."
                        )

                        await asyncio.sleep(delay)
                        continue

                    response.raise_for_status()

                    raw_data = response.json()

                    return APIResponse(
                        url=str(response.url),
                        data=raw_data,
                    )

                except httpx.RequestError:
                    if attempt == self.max_retries:
                        raise

                    delay = 2 ** attempt

                    print(
                        f"Request failed. "
                        f"Retrying in {delay} seconds..."
                    )

                    await asyncio.sleep(delay)

        raise RuntimeError(
            "Unexpected retry state"
        )