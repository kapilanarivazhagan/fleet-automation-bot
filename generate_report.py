"""
Static HTML Report Generator
Fetches data from Google Sheets, generates AI insight, and outputs a
self-contained, mobile-responsive HTML report page.
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import os

# ============================================================
# CONFIG
# ============================================================

load_dotenv()

SHEET_URL = "https://docs.google.com/spreadsheets/d/15xaEk5dqdfBjgFu4Auhr-HKioYsbhb0TrSw-eblOlEI/edit"
CREDS_FILE = "credentials.json"

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


# ============================================================
# DATA LAYER
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


def get_status_value(df, status):
    val = df[df["Status"] == status]["% of City Total"].mean()
    return 0.0 if pd.isna(val) else val * 100


def calculate_metrics(today_df, yday_df):
    m = {}
    m["on_today"] = round(get_status_value(today_df, "On Ground"), 1)
    m["serv_today"] = round(get_status_value(today_df, "Under Servicing (All)"), 1)
    m["rfd_today"] = round(get_status_value(today_df, "RFD"), 1)
    m["on_change"] = round(m["on_today"] - get_status_value(yday_df, "On Ground"), 2)
    m["serv_change"] = round(m["serv_today"] - get_status_value(yday_df, "Under Servicing (All)"), 2)
    m["rfd_change"] = round(m["rfd_today"] - get_status_value(yday_df, "RFD"), 2)
    return m


def detect_demand_risk():
    today = datetime.today()
    return "YES" if (today.weekday() >= 4 or today.day >= 26 or today.month in [10, 11]) else "NO"


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


def generate_ai_insight(metrics, risk_flag):
    metrics_text = (
        f"On Ground: {metrics['on_today']:.1f}% ({metrics['on_change']:+.1f}%)\n"
        f"Servicing: {metrics['serv_today']:.1f}% ({metrics['serv_change']:+.1f}%)\n"
        f"RFD: {metrics['rfd_today']:.1f}% ({metrics['rfd_change']:+.1f}%)"
    )
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": """You are a fleet operations strategist creating a short daily operations briefing.

STRICT OUTPUT FORMAT:

📊 Key Numbers

On Ground: <value>% (<+/- change>)
<one sentence explaining what the change means>

Servicing: <value>% (<+/- change>)
<one sentence explaining maintenance load>

RFD: <value>% (<+/- change>)
<one sentence explaining deployment readiness>

🧠 Insight
2–3 sentences explaining fleet health.

⚡ Action
Give clear operational actions:
- vehicles to deploy from RFD
- vehicles to close from servicing

ONLY include weekend/festival backup planning if risk flag = YES."""
            },
            {
                "role": "user",
                "content": f"Fleet metrics:\n\n{metrics_text}\n\nDemand risk flag: {risk_flag}\n\nGenerate briefing."
            }
        ]
    )
    return response.choices[0].message.content


# ============================================================
# HTML TEMPLATE
# ============================================================

def build_html(city, title, date_str, metrics, vehicle_df, ai_insight, risk_flag):

    # Build table rows
    table_headers = vehicle_df.columns.tolist()
    header_html = "".join(f"<th>{h}</th>" for h in table_headers)

    rows_html = ""
    for _, row in vehicle_df.iterrows():
        is_total = str(row.iloc[0]).lower() == "grand total"
        cls = ' class="total-row"' if is_total else ""
        cells = "".join(f"<td>{v}</td>" for v in row.values)
        rows_html += f"<tr{cls}>{cells}</tr>\n"

    # Format change arrows
    def fmt_change(val):
        arrow = "↑" if val >= 0 else "↓"
        color = "#4ade80" if val >= 0 else "#f87171"
        return f'<span style="color:{color}">{arrow} {val:+.1f}%</span>'

    # Risk badge
    risk_color = "#f87171" if risk_flag == "YES" else "#4ade80"
    risk_label = "⚠ Active" if risk_flag == "YES" else "✓ Normal"

    # Escape AI insight for HTML and add line breaks
    ai_html = ai_insight.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    ai_html = ai_html.replace("\n", "<br>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — {date_str}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background:
    linear-gradient(rgba(10,10,26,0.55), rgba(10,10,26,0.80)),
    url("../Ready-for-migrating-to-an-electric-vehicle-fleet.jpg");
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  color: #e2e8f0;
}}

  .container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 16px;
  }}


  /* Dashboard layout */

  .dashboard {{
    display: grid;
    grid-template-columns: 1.4fr 1fr;
    grid-template-rows: auto auto;
    gap: 16px;
    align-items: start;
  }}

  /* Left top */
  .metrics-section {{
    grid-column: 1;
    grid-row: 1;
  }}

  /* Left bottom */
  .table-section {{
    grid-column: 1;
    grid-row: 2;
  }}

  /* Right spanning both rows */
  .insight-section {{
    grid-column: 2;
    grid-row: 1 / span 2;
  }}

  /* Header */
  .header {{
    text-align: center;
    margin-bottom: 28px;
  }}
  .header h1 {{
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 6px;
  }}
  .header .date {{
    font-size: 0.85rem;
    color: #94a3b8;
  }}

  /* Metric Cards */
  .metrics {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 24px;
  }}
  .metric-card {{
    background: rgba(30, 41, 59, 0.65);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 14px;
  padding: 18px 16px;
  text-align: center;
  backdrop-filter: blur(12px);
  }}
  .metric-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
  }}
  .metric-card .label {{
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
    margin-bottom: 6px;
    font-weight: 600;
  }}
  .metric-card .value {{
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 4px;
  }}
  .metric-card .change {{
    font-size: 0.8rem;
    font-weight: 600;
  }}
  .metric-card.on-ground .value {{ color: #4ade80; }}
  .metric-card.on-ground {{ border-top: 3px solid #4ade80; }}
  .metric-card.servicing .value {{ color: #fbbf24; }}
  .metric-card.servicing {{ border-top: 3px solid #fbbf24; }}
  .metric-card.rfd .value {{ color: #60a5fa; }}
  .metric-card.rfd {{ border-top: 3px solid #60a5fa; }}

  /* Risk Badge */
  .risk-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid {risk_color}33;
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.75rem;
    font-weight: 600;
    color: {risk_color};
    margin-bottom: 20px;
  }}

  /* Table */
  .table-wrapper {{
    overflow-x: auto;
    border-radius: 14px;
    border: 1px solid rgba(148, 163, 184, 0.12);
    background: rgba(30, 41, 59, 0.5);
  }}
  table {{
    width: 100%;
    border-collapse: collapse;        
    font-size: 0.82rem;
    white-space: normal;
  }}
  th {{
    background: rgba(51, 65, 85, 0.8);
    color: #e2e8f0;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.68rem;
    letter-spacing: 0.06em;
    padding: 12px 14px;
    text-align: center;
    position: sticky;
    top: 0;
  }}
  th:first-child {{ text-align: left; }}
  td {{
    padding: 10px 14px;
    text-align: center;
    border-top: 1px solid rgba(148, 163, 184, 0.08);
  }}
  td:first-child {{
    text-align: left;
    font-weight: 500;
    color: #cbd5e1;
  }}
  tr:hover td {{ background: rgba(51, 65, 85, 0.3); }}
  .total-row td {{
    background: rgba(251, 191, 36, 0.12) !important;
    color: #fbbf24 !important;
    font-weight: 700;
    border-top: 2px solid rgba(251, 191, 36, 0.3);
  }}

  /* AI Insight */
  .insight-card {{
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 14px;
    padding: 22px 20px;
    backdrop-filter: blur(10px);
    border-left: 3px solid #a78bfa;
  }}
  .insight-card h2 {{
    font-size: 1rem;
    font-weight: 700;
    color: #a78bfa;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .insight-content {{
    font-size: 0.85rem;
    line-height: 1.75;
    color: #cbd5e1;
  }}

  /* Footer */
  .footer {{
    text-align: center;
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid rgba(148, 163, 184, 0.1);
    font-size: 0.7rem;
    color: #94a3b8;
    font-weight: 600;
  }}

  /* Mobile adjustments */
  @media (max-width: 768px) {{
      .dashboard {{
    grid-template-columns: 1fr;
  }}

  .metrics-section,
  .table-section,
  .insight-section {{
    grid-column: 1;
    grid-row: auto;
  }}
    .container {{ padding: 16px 12px; }}
    .header h1 {{ font-size: 1.1rem; }}
    .metrics {{ grid-template-columns: 1fr; }}
    .metric-card {{ padding: 14px 8px; }}
    .metric-card .value {{ font-size: 1.25rem; }}
    .metric-card .label {{ font-size: 0.6rem; }}
    .insight-card {{ padding: 16px 14px; }}
    table {{ font-size: 0.72rem; }}
    th, td {{ padding: 8px 10px; }}
  }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>{title}</h1>
    <div class="date">📅 {date_str}</div>
  </div>

  <div class="dashboard">

  <div class="metrics-section">

    <div class="metrics">
      <div class="metric-card on-ground">
        <div class="label">On Ground</div>
        <div class="value">{metrics['on_today']}%</div>
        <div class="change">{fmt_change(metrics['on_change'])}</div>
      </div>

      <div class="metric-card servicing">
        <div class="label">Servicing</div>
        <div class="value">{metrics['serv_today']}%</div>
        <div class="change">{fmt_change(metrics['serv_change'])}</div>
      </div>

      <div class="metric-card rfd">
        <div class="label">RFD</div>
        <div class="value">{metrics['rfd_today']}%</div>
        <div class="change">{fmt_change(metrics['rfd_change'])}</div>
      </div>
    </div>

    <div style="text-align:center">
      <span class="risk-badge">Demand Risk: {risk_label}</span>
    </div>

  </div>


  <div class="table-section">
    <div class="table-wrapper">
      <table>
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
  </div>


  <div class="insight-section">
    <div class="insight-card">
      <h2>🧠 AI Fleet Insight</h2>
      <div class="insight-content">{ai_html}</div>
    </div>
  </div>

</div>

  <div class="footer">
    Generated on {date_str} • Kapilan A • Data Scientist • Fyn Mobility
  </div>

</div>
</body>
</html>"""

    return html

# ============================================================
# MAIN
# ============================================================

def generate_city_report(city):
    titles = {
        "Combined three cities": "Three Cities Vehicle Status",
        "Bangalore": "Bangalore Vehicle Status",
        "Chennai": "Chennai Vehicle Status",
        "Hyderabad": "Hyderabad Vehicle Status",
    }

    print(f"📡 Loading Google Sheets data...")
    df = load_sheet()

    city_df = df.copy()
    if city != "Combined three cities":
        city_df = city_df[city_df["City"].str.lower() == city.lower()]

    unique_dates = sorted(city_df["Date"].unique())
    if len(unique_dates) < 2:
        print("❌ Not enough historical data.")
        return

    latest_date = unique_dates[-1]
    yesterday = unique_dates[-2]

    today_df = city_df[city_df["Date"] == latest_date]
    yday_df = city_df[city_df["Date"] == yesterday]

    print(f"📊 Calculating metrics...")
    metrics = calculate_metrics(today_df, yday_df)
    risk_flag = detect_demand_risk()

    print(f"🤖 Generating AI insight...")
    ai_insight = generate_ai_insight(metrics, risk_flag)

    print(f"📋 Building vehicle table...")
    vehicle_df = get_vehicle_table(df, city)

    title = titles.get(city, city)
    date_str = datetime.today().strftime("%d/%m/%Y")

    print(f"🎨 Building HTML page...")
    html = build_html(city, title, date_str, metrics, vehicle_df, ai_insight, risk_flag)

    filename = f"reports/{city.lower().replace(' ', '_')}_report.html"
    os.makedirs("reports", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Report saved: {filename}")
    return filename


if __name__ == "__main__":
    generate_city_report("Bangalore")