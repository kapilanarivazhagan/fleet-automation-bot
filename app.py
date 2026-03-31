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

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Fyn Fleet Reports", layout="wide")

# -----------------------------
# HEADER
# -----------------------------
st.markdown("<h1 style='text-align: center;'>Fyn Fleet Reports</h1>", unsafe_allow_html=True)
st.markdown("---")

# -----------------------------
# FILTER SECTION
# -----------------------------
city_display = st.selectbox("Select City", list(CITY_MAP.keys()))
city_key = CITY_MAP[city_display]

# Button BELOW filter
generate = st.button("Generate Report")

# -----------------------------
# MAIN ACTION
# -----------------------------
if generate:

    with st.spinner("Generating report..."):

        result = subprocess.run("python main.py", shell=True)

        if result.returncode != 0:
            st.error("Error running main.py")
            st.stop()

    st.success("Report generated successfully")

    # -----------------------------
    # FILE PATHS
    # -----------------------------
    image_path = f"reports/{city_key}_table.png"
    html_file = f"{city_key}_report.html"
    html_path = f"reports/{html_file}"

    if not os.path.exists(image_path) or not os.path.exists(html_path):
        st.error("Report files not found")
        st.stop()

    # -----------------------------
    # UPLOAD TO S3
    # -----------------------------
    with st.spinner("Uploading to S3..."):

        subprocess.run(f'aws s3 cp "{image_path}" s3://{S3_BUCKET}/{city_key}_table.png', shell=True)
        subprocess.run(f'aws s3 cp "{html_path}" s3://{S3_BUCKET}/{html_file}', shell=True)

    st.success("Upload complete")

    # -----------------------------
    # URL
    # -----------------------------
    html_url = f"{BASE_S3_URL}/{html_file}"

    # -----------------------------
    # DATE FORMAT
    # -----------------------------
    today_str = datetime.now().strftime("%d %B")

    # -----------------------------
    # LAYOUT (IMAGE + CAPTION)
    # -----------------------------
    col1, col2 = st.columns([3, 2])

    # IMAGE
    with col1:
        st.image(image_path, use_container_width=True)

    # CAPTION
    with col2:
        st.subheader("Caption")

        insight = "⚠️ Primary: High RFD limiting deployment.\n📈 Impact: +6% On Ground possible"

        caption = f"""📊 Fleet Status - {city_display} - {today_str}

{insight}

🔗 Full Report:
{html_url}
"""

        # Copy-enabled caption box
        components.html(f"""
            <textarea id="caption" style="width:100%;height:200px;">{caption}</textarea>
            <br><br>
            <button onclick="copyText()">Copy Caption</button>

            <script>
            function copyText() {{
                var copyText = document.getElementById("caption");
                copyText.select();
                document.execCommand("copy");
                alert("Copied!");
            }}
            </script>
        """, height=260)