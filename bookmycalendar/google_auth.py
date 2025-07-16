import os
import pickle
import streamlit as st
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
# Get TIMEZONE from Streamlit secrets (fallback to default)
TIMEZONE = st.secrets.get("timezone", "Asia/Kolkata")

def get_calendar_service():
    creds = None
    token_path = "token.pkl"

    # Load existing token if available
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If token not valid, refresh or create new
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Prepare secrets for InstalledAppFlow
            client_config = {
                "installed": {
                    "client_id": st.secrets["google_calendar"]["client_id"],
                    "client_secret": st.secrets["google_calendar"]["client_secret"],
                    "project_id": st.secrets["google_calendar"]["project_id"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost"]
                }
            }

            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the token for reuse
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)