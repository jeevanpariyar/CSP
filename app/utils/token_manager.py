import httpx
import os
import time
import random
import string
from dotenv import load_dotenv

load_dotenv()

class TokenManager:
    _token = None
    _expires = 0

    # For Production
    @classmethod
    async def get_token(cls):
        # if os.getenv("MODE") == "dev":
        #     return "mock_token_123"

        if cls._token and time.time() < cls._expires:
            return cls._token

        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{os.getenv('CSP_BASE_URL')}/get_token",
                json={
                    "username": os.getenv("CSP_USERNAME"),
                    "password": os.getenv("CSP_PASSWORD")
                },
                headers={"Content-Type": "application/json"}
            )
            data = res.json()
            cls._token = data["token"]
            cls._expires = time.time() + data.get("expires", 3600)
            return cls._token
        
    @classmethod
    async def generate_random_token(cls, length=10):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @classmethod
    async def generate_random_request_id(cls, length=12):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
