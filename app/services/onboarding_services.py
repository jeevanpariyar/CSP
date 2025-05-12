import os
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

credentialsDB = Path(os.getcwd() + "/" + os.getenv('cred_file'))

async def process_onboarding_form(form_data: dict):
    # Ensure the directory exists
    directory = os.path.dirname(credentialsDB)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    data = {}
    if os.path.exists(credentialsDB):
        try:
            with open(credentialsDB, "r") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
        except json.JSONDecodeError:
            # Log warning or reset the file
            print("Warning: Invalid JSON in cred.json. Overwriting with fresh data.")
            data = {}

    # Use email as key
    email = form_data["email"]
    data[email] = form_data

    # Write back to file
    with open(credentialsDB, "w") as f:
        json.dump(data, f, indent=4)

