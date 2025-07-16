import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
import json

SCOPES = ['https://www.googleapis.com/auth/calendar']
TIMEZONE = st.secrets.get("timezone", "Asia/Kolkata")

def get_calendar_service():
    creds = None

    # 🌐 Option 1: Use pre-authorized token in secrets (for production)
    if "google_calendar_token" in st.secrets:
        try:
            token_info = json.loads(st.secrets["google_calendar_token"])
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        except Exception as e:
            st.error("❌ Failed to load credentials from secrets.")
            st.exception(e)

    # 💻 Option 2: Fallback to local OAuth flow
    if not creds or not creds.valid:
        token_path = "token.pkl"

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
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

                # 💾 Save the token locally (optional, for future runs)
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)

                # 📋 Print the token JSON so user can copy it to secrets.toml
                st.write("👇 Copy the following into your secrets.toml under `google_calendar_token`:")
                st.code(json.dumps(json.loads(creds.to_json()), indent=2))

    return build('calendar', 'v3', credentials=creds)
