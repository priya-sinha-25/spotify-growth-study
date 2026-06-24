"""Prepare a Google Sheet CSV for Zapier analysis workflow."""

from pathlib import Path

import pandas as pd

INPUT_FILE = Path("master_feedback.csv")
OUTPUT_FILE = Path("feedback_for_zapier.csv")

COLUMNS = [
    "Original Review",
    "Source",
    "Primary Theme",
    "Discovery Related",
    "Frustration Summary",
    "User Segment",
    "Desired Behavior",
    "Key Insight",
    "Quote Worthy",
    "Analysis Status",
]


def main() -> None:
    df = pd.read_csv(INPUT_FILE)
    sheet_df = pd.DataFrame(
        {
            "Original Review": df["text"],
            "Source": df["source"],
            "Primary Theme": "",
            "Discovery Related": "",
            "Frustration Summary": "",
            "User Segment": "",
            "Desired Behavior": "",
            "Key Insight": "",
            "Quote Worthy": "",
            "Analysis Status": "pending",
        }
    )
    sheet_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(sheet_df)} rows to {OUTPUT_FILE}")
    print("Import this file into Google Sheets, then connect Zapier.")


if __name__ == "__main__":
    main()
