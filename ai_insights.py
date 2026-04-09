import json
import re
from config import client


# ============================================================
# SAFE JSON EXTRACTOR
# ============================================================

def extract_json(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
        return {}


# ============================================================
# BASE DETERMINISTIC LOGIC (UPDATED ELITE VERSION 🔥)
# ============================================================

def build_base_insight(
    metrics,
    vehicle_counts,
    rfd_reason,
    rfd_from_servicing,
    rfd_from_attrition,
    rfd_from_fleet_addition,
    rfd_daily_target,
    serv_daily_target,
    city,
    peak_on,
    rapido_daily_target
):

    on_change = vehicle_counts["on_today"] - vehicle_counts["on_yday"]
    rfd_change = vehicle_counts["rfd_today"] - vehicle_counts["rfd_yday"]
    serv_change = vehicle_counts["serv_today"] - vehicle_counts["serv_yday"]

    # ----------------------------
    # REFYND
    # ----------------------------
    refynd_today = vehicle_counts.get("refynd_today", 0)
    refynd_yday = vehicle_counts.get("refynd_yday", 0)

    # 🚨 detect NEW launch case
    is_new_refynd = refynd_yday == 0 and refynd_today > 0

    refynd_change = refynd_today - refynd_yday

    # CLEAN REFYND NOTE
    if is_new_refynd:
        refynd_note = "Refynd introduced into fleet."

    elif refynd_change > 0:
        refynd_note = f"Refynd increased by +{refynd_change} vehicles."

    elif refynd_change < 0:
        refynd_note = f"Refynd decreased by {abs(refynd_change)} vehicles."

    else:
        refynd_note = "Refynd remained stable."

    # ----------------------------
    # ON GROUND (ELITE)
    # ----------------------------
    today_on = vehicle_counts["on_today"]
    yday_on = vehicle_counts["on_yday"]

    vs_yday = today_on - yday_on
    gap_to_peak = max(0, peak_on - today_on)

    if vs_yday > 0:
        on_note = f"On Ground increased by +{vs_yday} compared to yesterday."

    elif vs_yday < 0:
        on_note = f"On Ground decreased by {abs(vs_yday)} compared to yesterday."

    else:
        on_note = "On Ground remained stable compared to yesterday."


    if not is_new_refynd and refynd_change > 0:
        on_note += f" Refynd contribution increased (+{refynd_change})."

    elif not is_new_refynd and refynd_change < 0:
        on_note += f" Refynd contribution declined ({refynd_change})."

    # ----------------------------
    # RFD (FINAL CORRECT LOGIC)
    # ----------------------------
    rfd_note = "RFD remained stable."

    if rfd_change > 0:

        parts = []

        if rfd_from_servicing > 0:
            parts.append(f"+{rfd_from_servicing} from servicing return")

        if rfd_from_attrition > 0:
            parts.append(f"+{rfd_from_attrition} from driver attrition")

        if rfd_from_fleet_addition > 0:
            parts.append(f"+{rfd_from_fleet_addition} from fleet addition")

        # 🔥 REFYND IMPACT (only if not new launch)
        if not is_new_refynd and refynd_change > 0:
            parts.append(f"+{refynd_change} from refynd")

        breakdown = ", ".join(parts)

        rfd_note = f"RFD increased by +{rfd_change} vehicles"
        if breakdown:
            rfd_note += f" ({breakdown})"


    elif rfd_change < 0:

        parts = []

        # 🔥 REFYND IMPACT (only if not new launch)
        if not is_new_refynd and refynd_change > 0:
            parts.append(f"refynd deployment")

        parts.append("improved deployment")

        reason = ", ".join(parts)

        rfd_note = f"RFD reduced by {abs(rfd_change)} vehicles due to {reason}."


    # ----------------------------
    # SERVICING (SHARP + REAL)
    # ----------------------------
    if serv_change > 0:
        servicing_note = (
            f"Servicing increased by +{abs(serv_change)} vehicles, elevating downtime and constraining available fleet supply."
        )
    elif serv_change < 0:
        servicing_note = (
            f"Servicing dropped by {abs(serv_change)} vehicles, easing downtime pressure and improving availability."
        )
    else:
        servicing_note = "Servicing remained broadly stable with no material change."

    if metrics["serv_nonrapido_change"] > 0:
        servicing_note += " Non-Rapido servicing is trending upward, increasing repair cost exposure."

    # ----------------------------
    # ----------------------------
    # OPERATIONAL INSIGHT (FINAL CLEAN)
    # ----------------------------
    gap_to_peak = max(0, peak_on - today_on)

    if vs_yday > 0 and gap_to_peak > 0:
        line1 = f"{city} improved by +{vs_yday} vs yesterday, but is still {gap_to_peak} vehicles below full deployment."
        line2 = "If this trend continues, deployment will gradually recover but has not yet reached optimal levels."

    elif vs_yday > 0 and gap_to_peak == 0:
        line1 = f"{city} improved by +{vs_yday} vs yesterday and is at current peak deployment."
        line2 = "If this trend continues, further growth beyond current peak is possible."

    elif vs_yday < 0:
        line1 = f"{city} declined by {abs(vs_yday)} vs yesterday, increasing the deployment gap."
        line2 = "If this trend continues, fleet availability will weaken further."

    else:
        line1 = f"{city} remained flat with no improvement in deployment gap."
        line2 = "If this continues, recovery will remain stalled."

    operational_insight = line1 + "\n\n" + line2
    # ----------------------------
    # ACTIONS (UNCHANGED FORMAT)
    # ----------------------------
    rfd_action = (
        f"Maintain +{rfd_daily_target} daily net additions to reduce RFD backlog and to stay on track with monthly targets"
    )

    service_action = (
        f"Close {rapido_daily_target} rapido servicing cases daily and "
        f"{serv_daily_target} non rapido servicing cases daily to control downtime and support monthly deployment targets"
    )

    return {
        "on_ground_note": on_note,
        "rfd_note": rfd_note,
        "servicing_note": servicing_note,
        "refynd_note": refynd_note,
        "operational_insight": operational_insight,
        "rfd_action": rfd_action,
        "service_action": service_action
    }


# ============================================================
# AI REPHRASER (UNCHANGED)
# ============================================================

def rephrase_with_ai(base_data):

    prompt = f"""
Rephrase the following fleet update lines.

Write like a fleet operations manager.
Be direct, concise, and action-oriented.
Avoid words like: experienced, witnessed, approximately, has been.
DO NOT replace the word "vehicles" with "units" or any other term.
Do NOT remove phrases like "recovery in progress".

STRICT RULES:
- Write like a fleet operations manager
- Be direct, concise, and action-oriented
- Avoid corporate or descriptive language
- Keep sentences short and factual
- DO NOT change ANY numbers
- DO NOT change + or - signs
- DO NOT add new information
- Keep total output under 1000 characters
- Always use the phrase "net additions" when referring to fleet increase actions
- Never use words like "add vehicles", "adding vehicles", or similar variations
- Do not simplify or rephrase "net additions"
- Do not add new explanations or trends not present in the input

DATA:
{json.dumps(base_data, indent=2)}

Return JSON in same structure.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            temperature=0.6,
            messages=[
                {"role": "system", "content": "You rephrase text without changing facts."},
                {"role": "user", "content": prompt}
            ]
        )

        ai_text = response.choices[0].message.content
        ai_data = extract_json(ai_text)

        for key in base_data:
            if key not in ai_data or not ai_data[key]:
                ai_data[key] = base_data[key]

        return ai_data

    except:
        return base_data


# ============================================================
# MAIN FUNCTION (ONLY CHANGE: PASS CITY)
# ============================================================

def generate_ai_insight(
    metrics,
    risk_flag,
    rfd_count,
    serv_count,
    days_left,
    movement_data,
    rfd_from_servicing,
    rfd_from_attrition,
    rfd_from_fleet_addition,
    city,
    is_weekend,
    vehicle_counts,
    rfd_reason,
    trend,
    rfd_daily_target,
    serv_daily_target,
    peak_on,
    rapido_daily_target  
):

    base_data = build_base_insight(
        metrics,
        vehicle_counts,
        rfd_reason,
        rfd_from_servicing,
        rfd_from_attrition,
        rfd_from_fleet_addition,
        rfd_daily_target,
        serv_daily_target,
        city,
        peak_on,
        rapido_daily_target   # ✅ ADD THIS
    )

    final_data = rephrase_with_ai(base_data)

    # 🔒 DO NOT let AI modify operational insight
    final_data["operational_insight"] = base_data["operational_insight"]

    final_data["backup_action"] = ""

    return final_data