from table_image_template import build_table_image
import imgkit
from datetime import datetime
import calendar 
import os

from data_loader import load_sheet, get_vehicle_table
from metrics import calculate_metrics, detect_demand_risk
from ai_insights import generate_ai_insight
from html_template import build_html


# ============================================================
# REPORT GENERATOR
# ============================================================

def generate_city_report(city):

    titles = {
        "Combined three cities": "Fleet Status - Three Cities",
        "Bangalore": "Fleet Status - Bangalore",
        "Chennai": "Fleet Status - Chennai",
        "Hyderabad": "Fleet Status - Hyderabad",
    }

    print("📡 Loading Google Sheets data...")
    df = load_sheet()

    city_df = df.copy()

    if city != "Combined three cities":
        city_df = city_df[city_df["City"].str.strip().str.lower() == city.lower()]

    unique_dates = sorted(city_df["Date"].unique())

    if len(unique_dates) < 2:
        print("❌ Not enough historical data.")
        return None

    latest_date = unique_dates[-1]

    on_history = (
        city_df[city_df["Status"] == "On Ground"]
        .groupby("Date")["Total"]
        .sum()
    )

    peak_on = int(on_history.max()) if not on_history.empty else 0
    

    # ============================================================
    # FIND LAST MEANINGFUL CHANGE DAY
    # ============================================================

    today_df = city_df[city_df["Date"] == latest_date]

    yesterday = None
    today_total = today_df["Total"].sum()

    for prev_date in reversed(unique_dates[:-1]):
        prev_df = city_df[city_df["Date"] == prev_date]
        prev_total = prev_df["Total"].sum()

        if today_total != prev_total:
            yesterday = prev_date
            break

    if yesterday is None:
        yesterday = unique_dates[-2]

    yday_df = city_df[city_df["Date"] == yesterday]

    print("Comparing:", latest_date.date(), "vs", yesterday.date())

    print("📊 Calculating metrics...")

    # 🔥 SINGLE SOURCE OF TRUTH
    vehicle_df = get_vehicle_table(df, city)
    vehicle_df_clean = vehicle_df[vehicle_df["Status"] != "Grand Total"]

    print("TODAY DF TOTAL:", today_df["Total"].sum())
    print("VEHICLE DF TOTAL:", vehicle_df["Total"].sum())  

    metrics = calculate_metrics(today_df, yday_df)

    # ============================================================
    # VEHICLE STATE COUNTS
    # ============================================================

    today_status = today_df.groupby("Status")["Total"].sum()
    yday_status = yday_df.groupby("Status")["Total"].sum()

    def get_status(series, names):
        for name in names:
            if name in series:
                return series[name]
        return 0

    today_on = get_status(today_status, ["On Ground"])
    today_rfd = get_status(today_status, ["RFD"])

    today_serv_rapido = get_status(
        today_status,
        ["Servicing - Rapido", "Servicing Rapido"]
    )

    today_serv_non = get_status(
        today_status,
        ["Servicing - Non Rapido", "Servicing Non Rapido"]
    )

    yday_on = get_status(yday_status, ["On Ground"])
    yday_rfd = get_status(yday_status, ["RFD"])

    yday_serv_rapido = get_status(
        yday_status,
        ["Servicing - Rapido", "Servicing Rapido"]
    )

    yday_serv_non = get_status(
        yday_status,
        ["Servicing - Non Rapido", "Servicing Non Rapido"]
    )

    # ============================================================
    # TOTAL FLEET SIZE
    # ============================================================

    today_total_fleet = today_df["Total"].sum()
    yday_total_fleet = yday_df["Total"].sum()

    fleet_change = today_total_fleet - yday_total_fleet

    # ============================================================
    # MOVEMENT CALCULATION
    # ============================================================

    move_on = today_on - yday_on
    move_rfd = today_rfd - yday_rfd
    move_serv_total = (today_serv_rapido + today_serv_non) - (yday_serv_rapido + yday_serv_non)

    movement_data = {
        "on_ground_change": move_on,
        "rfd_change": move_rfd,
        "servicing_change": move_serv_total
    }

    is_weekend = datetime.today().weekday() >= 5

    # ============================================================
    # RFD SOURCE BREAKDOWN
    # ============================================================

    rfd_from_servicing = 0
    rfd_from_attrition = 0
    rfd_from_fleet_addition = 0

    if move_rfd > 0:

        # Step 1: servicing contribution
        if move_serv_total < 0:
            rfd_from_servicing = min(abs(move_serv_total), move_rfd)

        # Step 2: attrition contribution
        remaining = move_rfd - rfd_from_servicing

        if move_on < 0:
            rfd_from_attrition = min(abs(move_on), remaining)

        # Step 3: fleet addition contribution
        remaining = move_rfd - rfd_from_servicing - rfd_from_attrition

        if fleet_change > 0:
            rfd_from_fleet_addition = min(fleet_change, remaining)

    # ============================================================
    # RFD REASON (NO AI GUESSING)
    # ============================================================

    if move_rfd < 0:
        if move_on >= abs(move_serv_total):
            rfd_reason = "deployment"
        else:
            rfd_reason = "servicing"

    elif move_rfd > 0:
        if move_on < 0:
            rfd_reason = "attrition"
        else:
            rfd_reason = "service_closure"

    else:
        rfd_reason = "no_change"

    # ============================================================
    # TREND LOGIC
    # ============================================================

    if move_on > 0 and move_rfd < 0:
        trend = "improving"
    elif move_on < 0 and move_rfd > 0:
        trend = "declining"
    else:
        trend = "stable"

    # ============================================================
    # VEHICLE TABLE
    # ============================================================

    print("📋 Building vehicle table...")
    vehicle_df = get_vehicle_table(df, city)
    vehicle_df_clean = vehicle_df[vehicle_df["Status"] != "Grand Total"]

    # ============================================================
    # BACKLOG + DAYS LEFT
    # ============================================================

    today_date = datetime.today()
    days_in_month = calendar.monthrange(today_date.year, today_date.month)[1]
    days_left = days_in_month - today_date.day + 1

    rfd_row = vehicle_df.loc[vehicle_df["Status"] == "RFD", "Total"]
    rfd_count = int(rfd_row.values[0]) if not rfd_row.empty else 0

    serv_row = vehicle_df.loc[
        vehicle_df["Status"] == "Under Servicing - Non Rapido", "Total"
    ]
    serv_count = int(serv_row.values[0]) if not serv_row.empty else 0

    # ============================================================
    # DAILY TARGETS (MONTH EXECUTION)
    # ============================================================

    rfd_daily_target = max(1, round(rfd_count / days_left + 4)) if days_left > 0 else 0
    serv_daily_target = max(1, round(serv_count / days_left + 2)) if days_left > 0 else 0

    # ============================================================
    # VEHICLE COUNTS (FOR AI NUMBERS)
    # ============================================================

    vehicle_counts = {
        "on_today": int(today_on),
        "on_yday": int(yday_on),
        "rfd_today": int(today_rfd),
        "rfd_yday": int(yday_rfd),
        "serv_today": int(today_serv_rapido + today_serv_non),
        "serv_yday": int(yday_serv_rapido + yday_serv_non)
    }

    risk_flag = detect_demand_risk(metrics)

    # ============================================================
    # AI INSIGHT
    # ============================================================

    print("🤖 Generating AI insight...")

    ai_data = generate_ai_insight(
        metrics,
        risk_flag,
        rfd_count,
        serv_count,
        days_left,
        movement_data,
        rfd_from_servicing,
        rfd_from_attrition,
        rfd_from_fleet_addition,   # ✅ MOVE HERE
        city,
        is_weekend,
        vehicle_counts,
        rfd_reason,
        trend,
        rfd_daily_target,
        serv_daily_target,
        peak_on
    )

    # ============================================================
    # BUILD TEXT
    # ============================================================

    backup_line = f"- {ai_data.get('backup_action','')}" if ai_data.get('backup_action') else ""

    ai_insight = f"""Key Metrics
1. On Ground: {metrics['on_today']:.2f}% ({metrics['on_change']:+.2f}%)
{ai_data['on_ground_note']}

2. RFD: {metrics['rfd_today']:.2f}% ({metrics['rfd_change']:+.2f}%)
{ai_data['rfd_note']}

3. Servicing:
Rapido {metrics['serv_rapido_today']:.2f}% ({metrics['serv_rapido_change']:+.2f}%),
Non-Rapido {metrics['serv_nonrapido_today']:.2f}% ({metrics['serv_nonrapido_change']:+.2f}%)
{ai_data['servicing_note']}

Operational Insights
{ai_data['operational_insight']}

Recommended Actions
- {ai_data['rfd_action']}
- {ai_data['service_action']}
{backup_line}
"""

    MAX_CHARS = 1950
    if len(ai_insight) > MAX_CHARS:
        ai_insight = ai_insight[:MAX_CHARS].rsplit(" ", 1)[0]

    title = titles.get(city, city)
    date_str = datetime.today().strftime("%d %B %Y")

    print("🎨 Building HTML page...")
    html = build_html(city, title, date_str, metrics, vehicle_df, ai_insight, risk_flag)

    filename = f"reports/{city.lower().replace(' ', '_')}_report.html"

    os.makedirs("reports", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Report saved: {filename}")

    # ============================================================
    # GENERATE TABLE IMAGE
    # ============================================================

    print("🖼️ Generating table image...")

    table_html = build_table_image(
        vehicle_df,
        title=f"{city} Vehicle Status",
        date_str=date_str
    )

    table_html_path = f"reports/{city.lower().replace(' ', '_')}_table.html"
    table_img_path = f"reports/{city.lower().replace(' ', '_')}_table.png"

    with open(table_html_path, "w", encoding="utf-8") as f:
        f.write(table_html)

    # Step 1: HTML → Image
    imgkit.from_file(
        table_html_path,
        table_img_path,
        options={
            "format": "png",    
            "encoding": "UTF-8",
            "quiet": "",
        }
    )

    # Step 2: 🔥 Auto-crop (your logic)
    import numpy as np
    from PIL import Image

    img = Image.open(table_img_path)

    img_np = np.array(img)

    # better detection
    gray = np.mean(img_np, axis=2)

    # stricter threshold
    mask = gray < 240

    if mask.any():
        coords = np.argwhere(mask)

        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0) + 1

        padding = 2
        y0 = max(y0 - padding, 0)
        x0 = max(x0 - padding, 0)
        y1 = min(y1 + padding, img_np.shape[0])
        x1 = min(x1 + padding, img_np.shape[1])

        img_cropped = Image.fromarray(img_np[y0:y1, x0:x1])
    else:
        img_cropped = img

    # overwrite image
    img_cropped.save(table_img_path)

    # ============================================================
    # Step 3: CLEANUP
    # ============================================================

    if os.path.exists(table_html_path):
        os.remove(table_html_path)

    print(f"✅ Table image saved (cropped): {table_img_path}")

    return filename


# ============================================================
# RUN ALL
# ============================================================

def generate_all_reports():

    cities = [
        "Combined three cities",
        "Bangalore",
        "Chennai",
        "Hyderabad"
    ]

    reports = []

    for city in cities:
        print("\n==============================")
        print(f"Generating report for {city}")
        print("==============================")

        report_file = generate_city_report(city)

        if report_file:
            reports.append(report_file)

    return reports


if __name__ == "__main__":
    generate_all_reports()