import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from config import settings

def get_gsheet_client():
    creds_dict = json.loads(settings.GOOGLE_SHEETS_CREDENTIALS_JSON)
    credentials = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(credentials)

def append_conversation_row(sheet_id: str, user_phone: str, user_input: str, bot_reply: str, contact_type: str):
    client = get_gsheet_client()
    sheet = client.open_by_key(sheet_id).sheet1
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [now, user_phone, user_input, bot_reply, contact_type]
    sheet.append_row(row, value_input_option="USER_ENTERED")
