from pydantic import BaseModel, Field

class CGRequest(BaseModel):
    offer_code: str = Field(..., example="OFFER123")
    msisdn: str = Field(..., example="encrypted_msisdn")
    source_ip: str = Field(..., example="192.168.1.1")
    user_agent: str = Field(..., example="Mozilla/5.0")
    requestid: str = Field(..., example="unique12345")
    redirect_url: str = Field(..., example="https://your-callback-url")