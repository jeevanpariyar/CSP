import os
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

credentialsDB = Path(os.getcwd() + "/" + os.getenv('cred_file'))
# credentialsDB = "C:/Users/akash_n5v05hg/Service API (SafariCom)/Documents/CSP/app/db/cred.json"

def load_credentials():
    if os.path.exists(credentialsDB):
        with open(credentialsDB, "r") as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
    return {}

def save_credentials(data: dict):
    directory = os.path.dirname(credentialsDB)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    with open(credentialsDB, "w") as f:
        json.dump(data, f, indent=4)

