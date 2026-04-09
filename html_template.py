# ============================================================
# HTML TEMPLATE
# ============================================================

def build_html(city, title, date_str, metrics, vehicle_df, ai_insight, risk_flag):

    # Build table rows
    table_headers = vehicle_df.columns.tolist()
    header_html = "".join(f"<th>{h}</th>" for h in table_headers)

    rows_html = ""

    for _, row in vehicle_df.iterrows():

        label = str(row.iloc[0]).lower()

        # highlight summary rows
        is_total = (
            "total" in label or
            "(all)" in label
        )

        cls = ' class="total-row"' if is_total else ""

        cells = "".join(f"<td>{v}</td>" for v in row.values)

        rows_html += f"<tr{cls}>{cells}</tr>\n"

    # Format change arrows
    def fmt_change(val, metric):

        if metric in ["util", "on"]:
            good = val > 0
        elif metric in ["rfd", "serv"]:
            good = val < 0
        else:
            good = False

        arrow = "↑" if val >= 0 else "↓"
        color = "#4ade80" if good else "#f87171"

        return f'<span style="color:{color}">{arrow} {val:+.1f}%</span>'

    # Fleet status badge
    status_map = {
        "CRITICAL": ("#ef4444", "Critical"),
        "RISK": ("#f87171", "⚠ Risk"),
        "HEALTHY": ("#4ade80", "Healthy")
    }

    # Safe assignment (prevents crashes)
    status_color, status_label = status_map.get(
        risk_flag,
        ("#94a3b8", "Unknown")
    )

    # Escape AI insight for HTML
    import re

    MAX_INSIGHT_CHARS = 950
    if len(ai_insight) > MAX_INSIGHT_CHARS:
        ai_insight = ai_insight[:MAX_INSIGHT_CHARS].rsplit(" ", 1)[0]

    ai_html = ai_insight.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # highlight numbers
    ai_html = re.sub(r'(\d+\.?\d*%)', r'<span class="ai-num">\1</span>', ai_html)
    ai_html = re.sub(r'(\d+ vehicles?)', r'<span class="ai-num">\1</span>', ai_html)

    ai_html = ai_html.replace("\n", "<br>")

    # highlight section headers
    headers = ["Key Metrics", "Operational Insights", "Recommended Actions"]

    for h in headers:
        ai_html = ai_html.replace(h, f'<span class="ai-header">{h}</span>')

    ai_html = ai_html.replace("\n", "<br>")

    # ADVANCED RISK LOGIC
    # ============================================================

    on = metrics["on_today"]
    rfd = metrics["rfd_today"]
    serv = metrics["serv_rapido_today"] + metrics["serv_nonrapido_today"]

    primary = ""
    secondary = ""
    impact = ""

    # 🔴 PRIMARY DRIVER
    if rfd > serv and rfd > 15:
        primary = f"High RFD ({rfd:.1f}%) limiting deployment"
    elif serv > rfd and serv > 20:
        primary = f"Servicing backlog ({serv:.1f}%) reducing availability"
    elif on < 60:
        primary = f"Low active fleet ({on:.1f}%) impacting demand"
    else:
        primary = "Fleet operating within stable limits"

    # 🟡 SECONDARY PRESSURE
    if primary.startswith("High RFD") and serv > 20:
        secondary = f"Servicing load also elevated ({serv:.1f}%)"
    elif primary.startswith("Servicing") and rfd > 15:
        secondary = f"RFD still contributing ({rfd:.1f}%)"
    elif primary.startswith("Low active") and rfd > 15:
        secondary = f"RFD restricting supply ({rfd:.1f}%)"

    # 📈 IMPACT ESTIMATION (simple heuristic)
    if primary.startswith("High RFD"):
        impact = f"Fixing this can improve On Ground by ~{round(rfd * 0.4,1)}%"
    elif primary.startswith("Servicing"):
        impact = f"Reducing backlog can improve availability by ~{round(serv * 0.3,1)}%"
    elif primary.startswith("Low active"):
        impact = "Improving deployment can directly lift revenue"

    # 🧾 FINAL CAPTION
    caption = f"⚠ Primary: {primary}."

    if secondary:
        caption += f" Secondary: {secondary}."

    if impact:
        caption += f" Impact: {impact}."

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — {date_str}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@600;700&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}

body {{
font-family:'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
background:
linear-gradient(rgba(10,10,26,0.55), rgba(10,10,26,0.80)),
url("../Ready-for-migrating-to-an-electric-vehicle-fleet.jpg");
background-size:cover;
background-position:center;
background-attachment:fixed;
color:#e2e8f0;
}}

.ai-header {{
  display:block;
  font-weight:700;
  color:#22c55e;
  margin-top:8px;
  margin-bottom:3px;
  border-bottom:1px solid rgba(148,163,184,0.15);
  padding-bottom:2px;
}}

.ai-num {{
  color: #60a5fa;
  font-weight: 700;
}}

.container {{
max-width:1400px;
margin:0 auto;
padding:16px;
}}

/* =============================================
   DESKTOP LAYOUT (unchanged)
   ============================================= */

.dashboard {{
display:grid;
grid-template-columns:1.4fr 1fr;
grid-template-rows:auto auto;
gap:10px;
align-items:start;
}}

.metrics-section {{
  grid-column: 1;
  grid-row: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}} 

.table-section {{ grid-column:1; grid-row:2; }}
.insight-section {{
  grid-column: 2;
  grid-row: 1 / span 2;
  max-height: calc(100vh - 140px);
  overflow: hidden;
}}

/* Hide mobile swiper on desktop */
.mobile-swiper-wrapper {{ display: none; }}

.header{{
text-align:center;
margin-bottom:28px;
}}

.dashboard-title{{
font-family:'Poppins',sans-serif;
font-size:2rem;
font-weight:600;
color:#e5e7eb;
letter-spacing:0.02em;
}}

.dashboard-date{{
font-size:0.9rem;
color:#94a3b8;
font-weight:500;
letter-spacing:0.05em;
}}

.metrics {{
display:grid;
grid-template-columns:repeat(4,1fr);
gap:12px;
margin-bottom:24px;
}}

.metric-card {{
background:rgba(30,41,59,0.65);
border:1px solid rgba(148,163,184,0.15);
border-radius:14px;
padding:18px 16px;
text-align:center;
backdrop-filter:blur(12px);
transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.metric-card:hover {{
transform:translateY(-2px);
box-shadow:0 8px 25px rgba(0,0,0,0.3);
}}

.metric-card .label {{
font-size:0.7rem;
text-transform:uppercase;
letter-spacing:0.08em;
color:#94a3b8;
margin-bottom:6px;
font-weight:600;
white-space: nowrap;
}}

.metric-card .value {{
font-size:1.6rem;
font-weight:700;
margin-bottom:4px;
}}

.metric-card .change {{
font-size:0.8rem;
font-weight:600;
}}

.metric-card.on-ground .value {{ color:#4ade80; }}
.metric-card.on-ground {{ border-top:3px solid #4ade80; }}

.metric-card.rfd .value {{ color:#60a5fa; }}
.metric-card.rfd {{ border-top:3px solid #60a5fa; }}

.metric-card.serv-rapido .value {{ color:#fbbf24; }}
.metric-card.serv-rapido {{ border-top:3px solid #fbbf24; }}

.metric-card.serv-nonrapido .value {{ color:#fb923c; }}
.metric-card.serv-nonrapido {{ border-top:3px solid #fb923c; }}

.risk-badge {{
display:inline-flex;
align-items:center;
gap:6px;
background:rgba(30,41,59,0.7);
border:1px solid {status_color};
border-radius:20px;
padding:6px 14px;
font-size:0.75rem;
font-weight:600;
color:{status_color};
margin-bottom:6px;
}}

.risk-caption {{
  margin-top: 8px;
  padding: 6px 10px;
  font-size: 0.78rem;
  font-weight: 700;          /* bold */
  border-radius: 8px;
  display: inline-block;
  line-height: 1.4;
  max-width: 100%;
  word-wrap: break-word;
  white-space: normal;
  overflow-wrap: anywhere;
  letter-spacing: 0.02em;
}}


/* 🔴 Critical */
.risk-critical {{
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.35);
}}

/* ⚠ Risk */
.risk-risk {{
  background: rgba(251, 191, 36, 0.12);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
}}

/* 🟢 Healthy */
.risk-healthy {{
  background: rgba(74, 222, 128, 0.12);
  color: #4ade80;
  border: 1px solid rgba(74, 222, 128, 0.3);
}}

.table-wrapper {{
overflow-x:auto;
border-radius:14px;
border:1px solid rgba(148,163,184,0.12);
background:rgba(30,41,59,0.5);
}}

table {{
width:100%;
border-collapse:collapse;
font-size:0.82rem;
}}

th {{
background:rgba(51,65,85,0.8);
font-weight:600;
text-transform:uppercase;
font-size:0.68rem;
letter-spacing:0.06em;
padding:12px 14px;
text-align:center;
position:sticky;
top:0;
}}

th:first-child {{ text-align:left; }}

td {{
padding:10px 14px;
text-align:center;
border-top:1px solid rgba(148,163,184,0.08);
}}

td:first-child {{
text-align:left;
font-weight:500;
color:#cbd5e1;
}}

tr:hover td {{ background:rgba(51,65,85,0.3); }}

.total-row td {{
background:rgba(251,191,36,0.12)!important;
color:#fbbf24!important;
font-weight:700;
border-top:2px solid rgba(251,191,36,0.3);
}}

.insight-card {{
background:rgba(30,41,59,0.7);
border:1px solid rgba(148,163,184,0.12);
border-radius:14px;
padding:22px 20px;
backdrop-filter:blur(10px);
border-left:3px solid #a78bfa;
height: 100%;
min-height: 0; 
display: flex;
flex-direction: column;
}}

.insight-card h2 {{
font-size:1rem;
font-weight:700;
color:#a78bfa;
margin-bottom:6px;
}}

.insight-content {{
font-size:0.85rem;
line-height:1.25;
color:#cbd5e1;
overflow-y: auto;
flex: 1;
padding-right: 6px;
scrollbar-width: thin;
scroll-behavior: smooth;
}}

.footer {{
text-align:center;
margin-top:10px;
padding-top:8px;
border-top:1px solid rgba(148,163,184,0.1);
font-size:0.7rem;
color:#94a3b8;
font-weight:600;
}}

/* =============================================
   TABLET & MOBILE SWIPER (≤ 1024px)
   ============================================= */

@media (max-width:1024px) {{

  /* Hide the desktop grid layout */
  .dashboard {{ display: none; }}

  /* Show the mobile swiper */
  .mobile-swiper-wrapper {{ display: block; }}

  /* ---- Swiper shell ---- */
  .swiper-outer {{
    position: relative;
    overflow: hidden;
    width: 100%;
    touch-action: pan-y;
  }}

  .swiper-track {{
    display: flex;
    width: 300%;           /* 3 panels × 100% */
    transition: transform 0.38s cubic-bezier(0.4, 0, 0.2, 1);
    will-change: transform;
  }}

  /* Each panel occupies 1/3 of the track = 100vw */
  .swiper-panel {{
    width: 33.3333%;
    flex-shrink: 0;
    padding: 0 2px;
  }}

  /* ---- Dot navigation ---- */
  .swiper-dots {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10px;
    margin: 0 0 14px 0;
  }}

  .swiper-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(148,163,184,0.3);
    border: 1px solid rgba(148,163,184,0.4);
    cursor: pointer;
    transition: all 0.25s ease;
  }}

  .swiper-dot.active {{
    background: #a78bfa;
    border-color: #a78bfa;
    transform: scale(1.35);
    box-shadow: 0 0 8px rgba(167,139,250,0.5);
  }}

  /* ---- Swipe hint label ---- */
  .swipe-hint {{
    text-align: center;
    font-size: 0.68rem;
    color: #475569;
    margin-bottom: 10px;
    letter-spacing: 0.05em;
  }}

  /* ---- Arrow nav buttons ---- */
  .swiper-arrows {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 4px;
    margin-bottom: 10px;
  }}

  .swiper-arrow {{
    background: rgba(30,41,59,0.7);
    border: 1px solid rgba(148,163,184,0.2);
    border-radius: 50%;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 1rem;
    color: #94a3b8;
    transition: all 0.2s ease;
    backdrop-filter: blur(8px);
    -webkit-tap-highlight-color: transparent;
    user-select: none;
  }}

  .swiper-arrow:active {{
    background: rgba(51,65,85,0.9);
    color: #e2e8f0;
    transform: scale(0.92);
  }}

  .swiper-arrow.disabled {{
    opacity: 0.2;
    pointer-events: none;
  }}

  /* Page counter in arrows row */
  .page-counter {{
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 600;
    letter-spacing: 0.06em;
  }}

  /* ---- Metrics panel adjustments ---- */
  .metrics {{
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 12px;
  }}

  /* ---- Insight panel scroll if tall ---- */
  .swiper-panel .insight-card {{
    max-height: none;
    overflow-y: visible;
  }}

}}

/* =============================================
   MOBILE EXTRA SMALL (≤ 600px)
   ============================================= */

@media (max-width:600px) {{

    body {{
    font-family:'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color:#e2e8f0;
    position: relative;
    min-height: 100vh;
    }}

    body::before {{
    content: '';
    position: fixed;
    inset: 0;
    background:
        linear-gradient(rgba(10,10,26,0.55), rgba(10,10,26,0.80)),
        url("../Ready-for-migrating-to-an-electric-vehicle-fleet.jpg");
    background-size: cover;
    background-position: center;
    z-index: -1;
    }}

  .container {{ padding: 10px; }}

  .dashboard-title {{ font-size: 1.5rem; }}

  .metrics {{
    grid-template-columns: 1fr;
    gap: 10px;
  }}

  .metric-card {{ padding: 14px 12px; }}
  .metric-card .value {{ font-size: 1.3rem; }}
  .metric-card .label {{ font-size: 0.65rem; }}

  table {{ font-size: 0.72rem; }}
  th, td {{ padding: 8px 8px; }}

  .insight-card {{ padding: 16px; }}

  .swiper-panel .insight-card {{
    max-height: none;
    overflow: visible;
  }}

}}
</style>
</head>

<body>

<div class="container">
  <div class="header">
    <h1 class="dashboard-title">{title}</h1>
    <div class="dashboard-date">{date_str}</div>
  </div>

  <!-- ==========================================
       DESKTOP GRID (hidden on tablet/mobile)
       ========================================== -->
  <div class="dashboard">

    <div class="metrics-section">
      <div class="metrics">
        <div class="metric-card on-ground">
          <div class="label">On Ground</div>
          <div class="value">{metrics['on_today']}%</div>
          <div class="change">{fmt_change(metrics['on_change'], "on")}</div>
        </div>
        <div class="metric-card rfd">
          <div class="label">RFD</div>
          <div class="value">{metrics['rfd_today']}%</div>
          <div class="change">{fmt_change(metrics['rfd_change'], "rfd")}</div>
        </div>
        <div class="metric-card serv-rapido">
          <div class="label">Servicing - Rapido</div>
          <div class="value">{metrics['serv_rapido_today']}%</div>
          <div class="change">{fmt_change(metrics['serv_rapido_change'], "serv")}</div>
        </div>
        <div class="metric-card serv-nonrapido">
          <div class="label">Servicing - Non Rapido</div>
          <div class="value">{metrics['serv_nonrapido_today']}%</div>
          <div class="change">{fmt_change(metrics['serv_nonrapido_change'], "serv")}</div>
        </div>
      </div>
      <div style="text-align:center">
        <span class="risk-badge">Fleet Status: {status_label}</span>
        <div class="risk-caption risk-{risk_flag.lower()}">{caption}</div>
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
        <h2>Fyn Fleet Insights</h2>
        <div class="insight-content">{ai_html}</div>
      </div>
    </div>

  </div><!-- /dashboard -->


  <!-- ==========================================
       MOBILE / TABLET SWIPER
       (visible only on ≤ 1024px via CSS)
       ========================================== -->
  <div class="mobile-swiper-wrapper">

    <!-- Dot indicators at top -->
    <div class="swiper-dots">
      <div class="swiper-dot active" data-index="0"></div>
      <div class="swiper-dot" data-index="1"></div>
      <div class="swiper-dot" data-index="2"></div>
    </div>

    <!-- Arrow nav + page counter -->
    <div class="swiper-arrows">
      <button class="swiper-arrow disabled" id="prevBtn" aria-label="Previous">&#8592;</button>
      <span class="page-counter" id="pageCounter">1 / 3</span>
      <button class="swiper-arrow" id="nextBtn" aria-label="Next">&#8594;</button>
    </div>

    <!-- Swipeable track -->
    <div class="swiper-outer" id="swiperOuter">
      <div class="swiper-track" id="swiperTrack">

        <!-- PAGE 1 — Metrics -->
        <div class="swiper-panel" id="panel-0">
          <div class="metrics">
            <div class="metric-card on-ground">
              <div class="label">On Ground</div>
              <div class="value">{metrics['on_today']}%</div>
              <div class="change">{fmt_change(metrics['on_change'], "on")}</div>
            </div>
            <div class="metric-card rfd">
              <div class="label">RFD</div>
              <div class="value">{metrics['rfd_today']}%</div>
              <div class="change">{fmt_change(metrics['rfd_change'], "rfd")}</div>
            </div>
            <div class="metric-card serv-rapido">
              <div class="label">Servicing - Rapido</div>
              <div class="value">{metrics['serv_rapido_today']}%</div>
              <div class="change">{fmt_change(metrics['serv_rapido_change'], "serv")}</div>
            </div>
            <div class="metric-card serv-nonrapido">
              <div class="label">Servicing - Non Rapido</div>
              <div class="value">{metrics['serv_nonrapido_today']}%</div>
              <div class="change">{fmt_change(metrics['serv_nonrapido_change'], "serv")}</div>
            </div>
          </div>
          <div style="text-align:center; margin-top:10px;">
            <span class="risk-badge">Fleet Status: {status_label}</span>
            <div class="risk-caption risk-{risk_flag.lower()}">{caption}</div>
          </div>
        </div>

        <!-- PAGE 2 — Vehicle Table -->
        <div class="swiper-panel" id="panel-1">
          <div class="table-wrapper">
            <table>
              <thead><tr>{header_html}</tr></thead>
              <tbody>{rows_html}</tbody>
            </table>
          </div>
        </div>

        <!-- PAGE 3 — AI Insights -->
        <div class="swiper-panel" id="panel-2">
          <div class="insight-card">
            <h2>Fyn Fleet Insights</h2>
            <div class="insight-content">{ai_html}</div>
          </div>
        </div>

      </div><!-- /swiper-track -->
    </div><!-- /swiper-outer -->

    <div class="swipe-hint">← swipe to navigate →</div>

  </div><!-- /mobile-swiper-wrapper -->


  <div class="footer">
    Kapilan A • Data Scientist • Fyn Mobility
  </div>

</div><!-- /container -->

<script>
(function() {{
  const TOTAL = 3;
  let current = 0;
  let startX = 0;
  let startY = 0;
  let isDragging = false;
  let isHorizontal = null;

  const track    = document.getElementById('swiperTrack');
  const outer    = document.getElementById('swiperOuter');
  const prevBtn  = document.getElementById('prevBtn');
  const nextBtn  = document.getElementById('nextBtn');
  const counter  = document.getElementById('pageCounter');
  const dots     = document.querySelectorAll('.swiper-dot');

  // ---- Go to slide ----
  function goTo(index) {{
    if (index < 0 || index >= TOTAL) return;
    current = index;
    track.style.transform = 'translateX(-' + (current * 33.3333) + '%)';

    // Dots
    dots.forEach(function(d) {{
      d.classList.toggle('active', parseInt(d.dataset.index) === current);
    }});

    // Arrows
    prevBtn.classList.toggle('disabled', current === 0);
    nextBtn.classList.toggle('disabled', current === TOTAL - 1);

    // Counter
    counter.textContent = (current + 1) + ' / ' + TOTAL;
  }}

  // ---- Arrow buttons ----
  prevBtn.addEventListener('click', function() {{ goTo(current - 1); }});
  nextBtn.addEventListener('click', function() {{ goTo(current + 1); }});

  // ---- Dot clicks ----
  dots.forEach(function(d) {{
    d.addEventListener('click', function() {{
      goTo(parseInt(d.dataset.index));
    }});
  }});

  // ---- Touch: start ----
  outer.addEventListener('touchstart', function(e) {{
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    isDragging = true;
    isHorizontal = null;
  }}, {{ passive: true }});

  // ---- Touch: move ----
  outer.addEventListener('touchmove', function(e) {{
    if (!isDragging) return;
    var dx = e.touches[0].clientX - startX;
    var dy = e.touches[0].clientY - startY;

    // Lock direction on first significant movement
    if (isHorizontal === null && (Math.abs(dx) > 5 || Math.abs(dy) > 5)) {{
      isHorizontal = Math.abs(dx) > Math.abs(dy);
    }}

    if (isHorizontal) {{
      e.preventDefault(); // prevent vertical scroll only when swiping sideways
    }}
  }}, {{ passive: false }});

  // ---- Touch: end ----
  outer.addEventListener('touchend', function(e) {{
    if (!isDragging) return;
    isDragging = false;

    if (!isHorizontal) return; // was a vertical scroll, ignore

    var dx = e.changedTouches[0].clientX - startX;
    var threshold = 50;

    if (dx < -threshold) {{
      goTo(current + 1);
    }} else if (dx > threshold) {{
      goTo(current - 1);
    }}
  }});

  // ---- Mouse drag (for tablet stylus / desktop test) ----
  outer.addEventListener('mousedown', function(e) {{
    startX = e.clientX;
    isDragging = true;
  }});
  outer.addEventListener('mouseup', function(e) {{
    if (!isDragging) return;
    isDragging = false;
    var dx = e.clientX - startX;
    if (dx < -60) goTo(current + 1);
    else if (dx > 60) goTo(current - 1);
  }});
  outer.addEventListener('mouseleave', function() {{ isDragging = false; }});

}})();
</script>

</body>
</html>
"""

    return html 