import pandas as pd
from datetime import datetime


# ============================================================
# METRIC HELPERS
# ============================================================

def get_status_value(df, status):
    val = df[df["Status"] == status]["% of City Total"].mean()
    return 0.0 if pd.isna(val) else val * 100


# ============================================================
# CALCULATE METRICS
# ============================================================

def calculate_metrics(today_df, yday_df):

    m = {}

    # ON GROUND
    m["on_today"] = round(get_status_value(today_df, "On Ground"), 2)
    m["on_change"] = round(
        m["on_today"] - get_status_value(yday_df, "On Ground"), 2
    )

    # RFD
    m["rfd_today"] = round(get_status_value(today_df, "RFD"), 2)
    m["rfd_change"] = round(
        m["rfd_today"] - get_status_value(yday_df, "RFD"), 2
    )

    # SERVICING - RAPIDO
    m["serv_rapido_today"] = round(
        get_status_value(today_df, "Under Servicing - Rapido"), 2
    )
    m["serv_rapido_change"] = round(
        m["serv_rapido_today"]
        - get_status_value(yday_df, "Under Servicing - Rapido"),
        2,
    )

    # SERVICING - NON RAPIDO
    m["serv_nonrapido_today"] = round(
        get_status_value(today_df, "Under Servicing - Non Rapido"), 2
    )
    m["serv_nonrapido_change"] = round(
        m["serv_nonrapido_today"]
        - get_status_value(yday_df, "Under Servicing - Non Rapido"),
        2,
    )

    return m


# ============================================================
# DEMAND RISK DETECTOR
# ============================================================

def detect_demand_risk(metrics):

    on = metrics["on_today"]
    rfd = metrics["rfd_today"]
    serv = metrics["serv_rapido_today"] + metrics["serv_nonrapido_today"]

    # 🔴 CRITICAL
    if on < 50 or rfd > 30 or serv > 30:
        return "CRITICAL"

    # ⚠ RISK
    if on < 60 or rfd > 20 or serv > 20:
        return "RISK"

    # 🟢 HEALTHY
    return "HEALTHY"