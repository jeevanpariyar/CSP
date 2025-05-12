from fastapi import APIRouter, HTTPException
from app.models.request_models import CGRequest
from app.utils.token_manager import TokenManager
from app.services.csp_service import call_consent_gateway
import httpx, os
from app.utils.logger import logger

router = APIRouter()

@router.post("/request-cg", tags=["Consent Gateway"])
async def request_consent_gateway(data: CGRequest):
    try:
        response = await call_consent_gateway(
            offer_code=data.offer_code,
            msisdn=data.msisdn,
            user_agent=data.user_agent,
            source_ip=data.source_ip,
            requestid=data.requestid,
            redirect_url=data.redirect_url
        )
        logger.info("CG Request Successful")
        return response

    except httpx.HTTPStatusError as e:
        logger.error(f"mFilterIt API responded with error: {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"mFilterIt Error: {e.response.text}"
        )

    except httpx.RequestError as e:
        logger.error(f"Request to mFilterIt failed: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail="Failed to connect to mFilterIt service"
        )

    except Exception as e:
        logger.exception("Unhandled exception in Consent Gateway request")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )
    


@router.get("/redirect-handler", tags=["Consent Gateway"])
async def redirect_handler(status: str = "", requestid: str = "", mf_id: str = ""):
    logger.info(f"Redirect Handler Called - status: {status}, requestid: {requestid}, mf_id: {mf_id}")
    return {"status": status, "requestid": requestid, "mf_id": mf_id}


