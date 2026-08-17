import os

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("MY_API_KEY")

if not api_key:
    raise ValueError("MY_API_KEY is not configured")

print("API key loaded successfully")