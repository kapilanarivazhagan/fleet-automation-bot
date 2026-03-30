import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from config import SHEET_URL, CREDS_FILE


# ============================================================
# LOAD GOOGLE SHEET
# ============================================================

def load_sheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scope)
    client_gs = gspread.authorize(creds)

    sheet = client_gs.open_by_url(SHEET_URL).sheet1
    records = sheet.get_all_records()

    df = pd.DataFrame(records)
    df.columns = df.columns.str.strip()

    if "% of City Total" in df.columns:
        df["% of City Total"] = (
            df["% of City Total"].astype(str).str.replace("%", "", regex=False)
        )
        df["% of City Total"] = pd.to_numeric(df["% of City Total"], errors="coerce") / 100

    df["Date"] = pd.to_datetime(df["Date"])

    return df


# ============================================================
# VEHICLE STATUS TABLE
# ============================================================

def get_vehicle_table(df, city):

    latest_date = df["Date"].max()
    vdf = df[df["Date"] == latest_date].copy()

    if city != "Combined three cities":
        vdf = vdf[vdf["City"].str.lower() == city.lower()]

    required = ["Status", "L5N Fast", "L5N Slow", "L5M Fast", "L5M Slow", "N1", "Total"]
    existing = [c for c in required if c in vdf.columns]

    vdf = vdf[existing]

    if city == "Combined three cities":
        vdf = vdf.groupby("Status", as_index=False).sum()

    status_order = [
        "On Ground", "RFD", "Under Servicing (All)",
        "Under Servicing - Rapido", "Under Servicing - Non Rapido",
        "Under Recovery", "Back-up"
    ]

    vdf["Status"] = pd.Categorical(vdf["Status"], categories=status_order, ordered=True)
    vdf = vdf.sort_values("Status")

    exclude = ["Under Servicing - Rapido", "Under Servicing - Non Rapido"]

    numeric_cols = [c for c in vdf.columns if c != "Status"]
    totals = vdf[~vdf["Status"].isin(exclude)][numeric_cols].sum()

    total_row = pd.DataFrame([["Grand Total"] + totals.tolist()], columns=vdf.columns)

    vdf = pd.concat([vdf, total_row], ignore_index=True)

    return vdf