import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.api_key = os.getenv("MY_API_KEY")

        self.api_timeout = float(
            os.getenv("API_TIMEOUT", "10")
        )

        self.max_retries = int(
            os.getenv("MAX_RETRIES", "3")
        )

        if not self.api_key:
            raise RuntimeError(
                "MY_API_KEY is not configured."
            )


settings = Settings()

# Backwards compatibility for existing code.
API_TIMEOUT = settings.api_timeout