# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This file is dedicated to the public domain under the CC0 1.0 Universal license.
#
# You can find the full license text here:
# https://creativecommons.org/publicdomain/zero/1.0/
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# REQUIREMENTS
# - Python version 3.12 or greater (not tested on lower versions)
# - The Python `venv` module (or any other virtual environment manager)

# SETUP
# The following instructions are intended for Linux systems but work similarly 
# in other environments (e.g., Anaconda).

# In the repository root directory, run

# $ python3 -m venv env
# $ source env/bin/activate
# $ pip install requests
# $ cp auth_flow.example.py auto_flow.py

# In `auth_flow.py`, update the file with the authentication credentials we provided.

# RUN the script with
# $  python auth_flow.py
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import time
from pprint import pprint

import requests


CLIENT_ID     = "<client_id>"
CLIENT_SECRET = "<client_secret>"
AUTH_BASE_URL = "https://rmcapi.auth.eu-central-1.amazoncognito.com"
API_BASE_URL  = "https://stq74hnyoh.execute-api.eu-central-1.amazonaws.com/production"
SCOPE         = "rmcapi/read"

# Token cache
access_token = None
token_expiry = 0

# Retry policy: 4 retries with exponential backoff (1, 2, 4, 8 seconds).
MAX_RETRIES = 4
INITIAL_BACKOFF_S = 1.0

# Rate limiting (403/429) and transient server errors are worth retrying.
RETRYABLE_STATUS = {403, 429, 500, 502, 503, 504}


def request_with_backoff(method, url, **kwargs):
    """Send a request, retrying retryable responses with exponential backoff."""
    delay = INITIAL_BACKOFF_S
    for attempt in range(MAX_RETRIES + 1):
        response = requests.request(method, url, **kwargs)
        if response.status_code in RETRYABLE_STATUS and attempt < MAX_RETRIES:
            print(f"Request failed with {response.status_code}; retrying in {delay:.0f}s...")
            time.sleep(delay)
            delay *= 2
            continue
        return response


def get_access_token():
    global access_token, token_expiry

    # Return token if still valid
    if access_token and token_expiry > time.time():
        return access_token

    payload = { 
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": SCOPE
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    print("Requesting access token...")
    resp = request_with_backoff("POST", AUTH_BASE_URL + "/oauth2/token", data=payload, headers=headers)
    resp.raise_for_status() # raises exception on non-success status codes
    print("Access token retrieved.")

    token_data = resp.json()
    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 3600) 
    # Refresh 1 minute early.
    token_expiry = time.time() + expires_in - 60

    return access_token


def query_catalog():
    token = get_access_token()
    headers = {
        "Authorization": f"{token}",
        "Content-Type": "application/json"
    }
    # Example payload; batch queries of up to 500 parts are supported.
    payload = {
        "part_number": ["PN1000", "PN-0500", "PN 07-23 "],

        "apply_filter_quantity": False, # default
        "ignore_empty_parts": False, # default

        "test_mode": True, # Enables test dataset.
    }
    url = f"{API_BASE_URL}/v1/catalog/query"
    response = request_with_backoff("POST", url, json=payload, headers=headers)
    
    # Retry once on 401 Unauthorized (token might have expired)
    if response.status_code == 401:
        token = get_access_token()
        headers["Authorization"] = f"{token}"
        response = request_with_backoff("POST", url, json=payload, headers=headers)
    
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    try:
        result = query_catalog()
        pprint(result)
    except Exception as e:
        print("Error during catalog query:", e)
