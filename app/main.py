import os
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from app.utils.token_manager import TokenManager
from app.utils.cred_manegar import load_credentials, save_credentials
from app.services.csp_service import call_consent_gateway
from app.services.onboarding_services import process_onboarding_form
import uvicorn
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# CSP Subcribe 
@app.get("/", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# CSP OnBoard
@app.get("/onboard", response_class=HTMLResponse)
async def onboarding_form(request: Request):
    return templates.TemplateResponse("onBoarding.html", {"request": request})

# CSP Login
@app.get("/csp-login", response_class=HTMLResponse)
async def csp_login_form(request: Request):
    return templates.TemplateResponse("cspLogin.html", {"request": request})

# CSP Get Token
@app.get("/csp-token", response_class=HTMLResponse)
async def token_page(request: Request, token: str = "", expires: str = ""):
    return templates.TemplateResponse("cspToken.html", {"request": request, "token": token,"expires": expires})


# CSP CG
@app.get("/csp-cg")
async def consent_gateway(request: Request, requestid: str, redirect_url: str):
    return templates.TemplateResponse("consentGateway.html", {"request": request, "requestid": requestid, "redirect_url": redirect_url})

# APIs

# OnBoard API
@app.post("/onboard")
async def handle_onboarding(
    request: Request,
    csp_name: str = Form(...),
    csp_id: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    contact_person: str = Form(""),
    contact_number: str = Form(""),
    address: str = Form("")
):
    form_data = {
        "csp_name": csp_name,
        "csp_id": csp_id,
        "email": email,
        "password": password,
        "contact_person": contact_person,
        "contact_number": contact_number,
        "address": address
    }
    await process_onboarding_form(form_data)
    return templates.TemplateResponse("onboardingSuccess.html", {"request": request, "csp_name": csp_name})

# Login API
@app.post("/csp-login")
async def csp_login(request: Request, username: str = Form(...), password: str = Form(...)):
    data = {
        "username": username,
        "password": password
    }
    token_data = await csp_get_token(request, data)
    token_json = token_data.body.decode("utf-8")
    token_info = json.loads(token_json)

    return RedirectResponse(
        url=f"/csp-token?token={token_info['token']}&expires={token_info['expires']}",
        status_code=302
    )

# Get Token API
@app.post("/csp/get_token")
async def csp_get_token(request: Request, data: dict):
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required.")
    credentials = load_credentials()
    user = credentials.get(username)
    if not user or user.get("password") != password:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    
    # Generate new token & 5-minute expiry
    token = await TokenManager.generate_random_token()
    expiry = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    
    # Capturing User Agent & Source IP
    user_agent = request.headers.get("user-agent", "")
    source_ip = request.client.host

    # # Update and save
    user["token"] = token
    user["expires"] = expiry
    user["user_agent"] = user_agent
    user["source_ip"] = source_ip
    credentials[username] = user
    save_credentials(credentials)

    return JSONResponse({
        "token": token,
        "auth_type": "Bearer",
        "expires": expiry
    })


# Subscribe API
@app.post("/subscribe")
async def subscribe(
    request: Request,
    msisdn: str = Form(...),
    offer_code: str = Form(...)):

    credentials = load_credentials()
    user = None
    for uname, udata in credentials.items():
        if udata.get("contact_number") == msisdn:
            user = udata
            break

    if not user:
        raise HTTPException(status_code=404, detail="MSISDN not registered.")

    # Check token
    token = user.get("token")
    expiry = user.get("expires")

    if not token or not expiry or datetime.fromisoformat(expiry) < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token expired or missing.")

    # Validate user-agent and IP
    current_user_agent = request.headers.get("user-agent", "")
    current_ip = request.client.host

    if user.get("user_agent") != current_user_agent or user.get("source_ip") != current_ip:
        raise HTTPException(status_code=403, detail="User-Agent or IP mismatch.")

    # Generate request ID and save offer details
    request_id = await TokenManager.generate_random_request_id()
    user["offer_code"] = offer_code
    user["request_id"] = request_id

    save_credentials(credentials)

    # Redirect to CG
    redirect_url = str(request.url_for("redirect_handler"))
    cg_url = str(request.url_for("consent_gateway")) + f"?requestid={request_id}&redirect_url={redirect_url}"

    return RedirectResponse(cg_url, status_code=302)


# CSP Redirect API    
@app.get("/api/redirect-handler", response_class=HTMLResponse)
async def redirect_handler(request: Request, status: str = "", requestid: str = ""):
    credentials = load_credentials()
    found = False

    for username, user in credentials.items():
        if user.get("request_id") == requestid:
            user["consent_status"] = status
            save_credentials(credentials)
            found = True
            break

    if not found:
        status = "invalid"

    return templates.TemplateResponse("consentResult.html", {
        "request": request,
        "status": status
    })

# Use on Actual Safari API
# @app.post("/subscribe")
# async def subscribe(
#     request: Request,
#     msisdn: str = Form(...),
#     offer_code: str = Form("OFFER_TEST_001")):
#     user_agent = request.headers.get("user-agent", "")
#     source_ip = request.client.host
#     request_id = "REQ123456"  # Normally use a UUID or timestamp
#     redirect_url = str(request.url_for("redirect_handler"))
    
#     response = await call_consent_gateway(
#         offer_code=offer_code,
#         msisdn=msisdn,
#         user_agent=user_agent,
#         source_ip=source_ip,
#         requestid=request_id,
#         redirect_url=redirect_url
#     )
#     cg_url = response["cg_url"]
#     return RedirectResponse(cg_url, status_code=302)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    
    