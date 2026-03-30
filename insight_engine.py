# ============================================================
# FLEET INSIGHT ENGINE
# Rule-based operational reasoning
# ============================================================

# ============================================================
# FLEET INSIGHT ENGINE
# Rule-based operational reasoning
# ============================================================

def generate_fleet_logic(metrics):

    on_change = metrics["on_change"]
    rfd_change = metrics["rfd_change"]
    serv_r_change = metrics["serv_rapido_change"]
    serv_nr_change = metrics["serv_nonrapido_change"]

    servicing_change = serv_r_change + serv_nr_change

    trend = ""
    cause = ""
    evidence = ""
    risk = ""
    priority = ""

    # ============================================================
    # ON GROUND DECLINING
    # ============================================================

    if on_change < 0:

        trend = "Fleet availability declining."

        # CASE 1 — Servicing increased
        if servicing_change > 0 and abs(servicing_change) >= abs(on_change):

            cause = "vehicles moved into servicing"
            evidence = "Servicing levels increased while On Ground declined."
            risk = "Higher servicing load may reduce available fleet supply."
            priority = "Accelerate servicing closure to restore fleet availability."

        # CASE 2 — RFD increased (attrition likely)
        elif rfd_change > 0 and servicing_change <= 0:

            cause = "likely driver attrition"
            evidence = "On Ground declined while RFD increased without servicing growth."
            risk = "Driver availability may be reducing active fleet capacity."
            priority = "Investigate driver attrition and improve redeployment."

        # CASE 3 — unclear cause
        else:

            cause = "fleet movement across operational states"
            evidence = "Metric changes do not clearly indicate servicing or attrition."
            risk = "Fleet availability may fluctuate if underlying causes persist."
            priority = "Review deployment, servicing, and driver activity."

    # ============================================================
    # ON GROUND IMPROVING
    # ============================================================

    elif on_change > 0:

        trend = "Fleet availability improving."

        if rfd_change < 0:
            cause = "RFD vehicles deployed into operations"
            evidence = "RFD backlog reduced while On Ground increased."
        else:
            cause = "additional vehicles activated into the fleet"
            evidence = "On Ground increased without RFD reduction."

        risk = "Sustaining deployment efficiency will be important."
        priority = "Continue converting RFD vehicles into active fleet."

    # ============================================================
    # STABLE FLEET
    # ============================================================

    else:

        trend = "Fleet availability stable."

        if rfd_change > 0:
            cause = "RFD backlog increasing"
            evidence = "More vehicles waiting for deployment."
            risk = "Deployment delays may slow utilization."
            priority = "Improve deployment speed."

        elif servicing_change > 0:
            cause = "servicing pressure increasing"
            evidence = "Servicing levels rising while On Ground stable."
            risk = "Maintenance backlog may impact fleet availability."
            priority = "Increase servicing throughput."

        else:
            cause = "fleet balance stable"
            evidence = "No significant shifts across operational states."
            risk = "No immediate operational risk."
            priority = "Maintain current deployment and servicing balance."

    logic_summary = f"""
Trend: {trend}
Cause: {cause}
Evidence: {evidence}
Risk: {risk}
Priority: {priority}
"""

    return logic_summary