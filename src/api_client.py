import os
import httpx

import requests
from dotenv import load_dotenv


load_dotenv()

BASE_URL = "https://httpbin.org"
API_KEY = os.getenv("MY_API_KEY")

if not API_KEY:
    raise RuntimeError("MY_API_KEY is not configured")


def request(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json: dict | None = None,
) -> dict:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    response = requests.request(
        method,
        f"{BASE_URL}{path}",
        params=params,
        json=json,
        headers=headers,
    )

    response.raise_for_status()

    return response.json()


def get_request() -> dict:
    return request("GET", "/get")


def create_request(data: dict) -> dict:
    return request("POST", "/post", json=data)


def search_request(name: str) -> dict:
    return request(
        "GET",
        "/get",
        params={"name": name},
    )


def get_resource(resource_id: int) -> dict:
    return request(
        "GET",
        f"/anything/{resource_id}",
    )

async def fetch_data_async(
    client: httpx.AsyncClient,
    url: str,
) -> dict:
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPError as error:
        print(f"HTTP request failed: {error}")
        raise

import requests


def get_data(url: str) -> dict:
    try:
        response = requests.get(
            url,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as error:
        print(f"Request failed: {error}")
        raise

def get_customer(url: str, customer_id: int) -> dict:
    response = requests.get(
        url,
        params={"customer_id": customer_id},
    )

    response.raise_for_status()

    return response.json()

def create_request(url: str, data: dict) -> dict:
    response = requests.post(
        url,
        json=data,
    )

    response.raise_for_status()

    return response.json()

def update_data(url: str, data: dict) -> dict:
    response = requests.patch(
        url,
        json=data,
    )

    response.raise_for_status()

    return response.json()

def delete_data(url: str) -> dict:
    response = requests.delete(url)

    response.raise_for_status()

    return response.json()