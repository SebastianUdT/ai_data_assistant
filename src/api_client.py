from typing import Any

import requests

from src.config import API_TIMEOUT


def get_data(url: str) -> dict[str, Any]:
    response = requests.get(
        url,
        timeout=API_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()


def create_request(data: dict[str, Any]) -> dict[str, Any]:
    url = "https://httpbin.org/post"

    response = requests.post(
        url,
        json=data,
        timeout=API_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()