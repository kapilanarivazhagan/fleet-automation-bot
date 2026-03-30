import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="DSR Sales Dashboard", layout="wide")

st.title("📊 DSR Operations Dashboard")

uploaded_file = st.file_uploader("Upload DSR Excel File", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # ------------------------------------------------
    # KPIs
    # ------------------------------------------------

    total_revenue = df["Total_sale"].sum()
    total_orders = df["Total_bill"].sum()
    aov = total_revenue / total_orders if total_orders != 0 else 0

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Revenue", f"₹{total_revenue:,.0f}")
    col2.metric("Total Orders", f"{total_orders:,.0f}")
    col3.metric("Average Order Value", f"₹{aov:,.0f}")

    st.divider()

    # ------------------------------------------------
    # Prepare data
    # ------------------------------------------------

    outlet_sales = (
        df.groupby("Outlet")["Total_sale"]
        .sum()
        .reset_index()
        .sort_values(by="Total_sale", ascending=False)
    )

    daily_sales = (
        df.groupby("Date")["Total_sale"]
        .sum()
        .reset_index()
        .sort_values("Date")
    )

    # ------------------------------------------------
    # Charts side-by-side
    # ------------------------------------------------

    col1, col2 = st.columns(2)

    # Bar Chart
    with col1:

        st.subheader("🏬 Revenue by Outlet")

        fig_bar = px.bar(
            outlet_sales,
            x="Outlet",
            y="Total_sale",
            text="Total_sale",
        )

        fig_bar.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.0f}"
        )

        fig_bar.update_layout(
            yaxis_title="Revenue (₹)",
            xaxis_title="Outlet",
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    # Line Chart
    with col2:

        st.subheader("📈 Daily Revenue Trend")

        fig_line = px.line(
            daily_sales,
            x="Date",
            y="Total_sale",
            markers=True
        )

        fig_line.update_traces(
            hovertemplate="Date: %{x}<br>Revenue: ₹%{y:,.0f}"
        )

        fig_line.update_layout(
            yaxis_title="Revenue (₹)",
            xaxis_title="Date"
        )

        st.plotly_chart(fig_line, use_container_width=True)

else:

    st.info("Upload a cleaned DSR Excel file to view dashboard.")