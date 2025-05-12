import os
import httpx
from app.utils.token_manager import TokenManager


async def request_gateway(payload: dict, token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.getenv('CSP_BASE_URL')}/request_cg",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def call_consent_gateway(offer_code, msisdn, user_agent, source_ip, requestid, redirect_url):
    token = await TokenManager.get_token()
    payload = {
        "offer_code": offer_code,
        "msisdn": msisdn,
        "user_agent": user_agent,
        "source_ip": source_ip,
        "requestid": requestid,
        "redirect_url": redirect_url
    }
    return await request_gateway(payload, token)
