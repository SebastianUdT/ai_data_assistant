import asyncio

import httpx

from src.api_client import fetch_data_async


async def main():
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            fetch_data_async(
                client,
                "https://httpbin.org/get?request=one",
            ),
            fetch_data_async(
                client,
                "https://httpbin.org/get?request=two",
            ),
            fetch_data_async(
                client,
                "https://httpbin.org/get?request=three",
            ),
        )

        for result in results:
            print(result["args"])


if __name__ == "__main__":
    asyncio.run(main())