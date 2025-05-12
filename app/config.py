import os
from dotenv import load_dotenv

load_dotenv()

CSP_BASE_URL = os.getenv("CSP_BASE_URL")
USERNAME = os.getenv("CSP_USERNAME")
PASSWORD = os.getenv("CSP_PASSWORD")
REDIRECT_URL = os.getenv("REDIRECT_URL")
