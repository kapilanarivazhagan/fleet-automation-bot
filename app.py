import streamlit as st
import subprocess
import os
from datetime import datetime
import streamlit.components.v1 as components

# -----------------------------
# CONFIG
# -----------------------------
S3_BUCKET = "fleet-reports-kavi-001"
BASE_S3_URL = f"https://{S3_BUCKET}.s3.amazonaws.com"

CITY_MAP = {
    "Combined Three Cities": "combined_three_cities",
    "Bangalore": "bangalore",
    "Chennai": "chennai",
    "Hyderabad": "hyderabad",
    "All": "all"
}

# Clean display names
DISPLAY_NAME_MAP = {
    "combined_three_cities": "Three Cities",
    "bangalore": "Bangalore",
    "chennai": "Chennai",
    "hyderabad": "Hyderabad"
}

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Fyn Fleet Insight Reports", layout="wide")

# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    "<h1 style='text-align: center;'>Fyn Fleet Insight Reports</h1>",
    unsafe_allow_html=True
)
st.markdown("---")

# -----------------------------
# FUNCTION: RENDER CITY BLOCK
# -----------------------------
def render_city_block(city_display, city_key, html_url):

    image_path = f"reports/{city_key}_table.png"

    today_str = datetime.now().strftime("%d %B")

    caption = f"""📊 Fleet Status - {city_display} - {today_str}

🔗 Full Report:
{html_url}
"""

    safe_caption = caption.replace("`", "\\`")

    # ✅ City Subheader
    st.markdown(f"## 📍 {city_display}")

    col1, col2 = st.columns([3, 2])

    # -----------------------------
    # IMAGE
    # -----------------------------
    with col1:
        st.image(image_path, use_container_width=True)

    # -----------------------------
    # CAPTION (PRO UI)
    # -----------------------------
    with col2:
        st.markdown("### Caption")

        components.html(f"""
            <div style="
                position: relative;
                border: 1px solid #e6e6e6;
                border-radius: 12px;
                padding: 16px;
                background-color: #fafafa;
                font-family: system-ui;
            ">

                <button onclick="copyText()"
                style="
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background-color: #111;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 12px;">
                    Copy
                </button>

                <!-- Toast Notification -->
                <div id="toast" style="
                    position: absolute;
                    top: 10px;
                    right: 70px;
                    background-color: #4CAF50;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 6px;
                    font-size: 12px;
                    display: none;
                ">
                    Copied ✅
                </div>

                <pre id="captionText" style="
                    white-space: pre-wrap;
                    font-size: 14px;
                    margin-top: 25px;
                    line-height: 1.5;
                ">{safe_caption}</pre>

            </div>

            <script>
            function copyText() {{
                const text = document.getElementById("captionText").innerText;
                navigator.clipboard.writeText(text);

                const toast = document.getElementById("toast");
                toast.style.display = "block";

                setTimeout(() => {{
                    toast.style.display = "none";
                }}, 1500);
            }}
            </script>
        """, height=260)

    st.markdown("---")


# -----------------------------
# FILTER SECTION
# -----------------------------
city_display = st.selectbox("Select City", list(CITY_MAP.keys()))
city_key = CITY_MAP[city_display]

generate = st.button("Generate Report")

# -----------------------------
# MAIN ACTION
# -----------------------------
if generate:

    # -----------------------------
    # RUN SCRIPT
    # -----------------------------
    with st.spinner("Generating report..."):
        result = subprocess.run("python main.py", shell=True)

        if result.returncode != 0:
            st.error("Error running main.py")
            st.stop()

    st.success("Report generated successfully")

    # -----------------------------
    # CITY ORDER FIXED
    # -----------------------------
    if city_key == "all":
        cities_to_show = [
            "combined_three_cities",
            "bangalore",
            "chennai",
            "hyderabad"
        ]
    else:
        cities_to_show = [city_key]

    # -----------------------------
    # LOOP THROUGH CITIES
    # -----------------------------
    for city in cities_to_show:

        image_path = f"reports/{city}_table.png"
        html_file = f"{city}_report.html"
        html_path = f"reports/{html_file}"

        if not os.path.exists(image_path) or not os.path.exists(html_path):
            st.error(f"Missing files for {city}")
            continue

        # -----------------------------
        # UPLOAD TO S3
        # -----------------------------
        with st.spinner(f"Uploading {DISPLAY_NAME_MAP[city]} to S3..."):

            subprocess.run(
                f'aws s3 cp "{image_path}" s3://{S3_BUCKET}/reports/{city}_table.png',
                shell=True
            )

            subprocess.run(
                f'aws s3 cp "{html_path}" s3://{S3_BUCKET}/reports/{html_file}',
                shell=True
            )

        html_url = f"{BASE_S3_URL}/reports/{html_file}"

        # -----------------------------
        # RENDER BLOCK
        # -----------------------------
        render_city_block(
            city_display=DISPLAY_NAME_MAP[city],
            city_key=city,
            html_url=html_url
        )

    st.success("✅ All reports processed successfully")