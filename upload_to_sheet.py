"""Upload master_feedback.csv to Google Sheets."""

import sys
from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1wDVsss7RExqOrkN80bick2Ot01Tc6_rXUwLIKw3xBrM"
INPUT_FILE = Path("master_feedback.csv")
CREDENTIALS_FILE = Path("credentials.json")
GSPREAD_DIR = Path.home() / "AppData" / "Roaming" / "gspread"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client() -> gspread.Client:
    if CREDENTIALS_FILE.exists():
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        return gspread.authorize(creds)

    GSPREAD_DIR.mkdir(parents=True, exist_ok=True)
    oauth_credentials = GSPREAD_DIR / "credentials.json"
    if not oauth_credentials.exists() and CREDENTIALS_FILE.exists():
        oauth_credentials.write_text(CREDENTIALS_FILE.read_text(encoding="utf-8"), encoding="utf-8")

    if not oauth_credentials.exists():
        print(
            "Google Sheets credentials not found.\n\n"
            "Option A - Automated upload:\n"
            "1. Go to https://console.cloud.google.com/apis/credentials\n"
            "2. Create OAuth client ID (Desktop app) or a service account\n"
            "3. Enable Google Sheets API and Google Drive API\n"
            "4. Save the JSON key as credentials.json in this folder\n"
            "5. If using a service account, share the Google Sheet with the service account email\n"
            "6. Run: python upload_to_sheet.py\n\n"
            "Option B - Manual import:\n"
            "1. Open your Google Sheet\n"
            "2. File > Import > Upload > master_feedback_for_sheet.csv\n"
            "3. Choose 'Replace current sheet' or 'Insert new rows'\n"
        )
        sys.exit(1)

    return gspread.oauth(scopes=SCOPES)


def load_feedback() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE)
    return df[["text", "source"]].rename(
        columns={"text": "Original Review", "source": "Source"}
    )


def upload_feedback() -> None:
    df = load_feedback()
    client = get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.sheet1

    headers = [["Original Review", "Source"]]
    rows = df.values.tolist()
    worksheet.clear()
    worksheet.update(headers + rows, value_input_option="USER_ENTERED")

    print(f"Uploaded {len(rows)} rows to '{spreadsheet.title}'.")


if __name__ == "__main__":
    upload_feedback()
