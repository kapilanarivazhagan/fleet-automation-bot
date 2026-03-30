from config import client


# ============================================================
# AI INSIGHT GENERATION
# ============================================================

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