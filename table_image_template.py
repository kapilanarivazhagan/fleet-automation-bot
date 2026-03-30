def build_table_image(vehicle_df, title="Vehicle Status", date_str=""):

    df = vehicle_df.copy()

    # 🎯 Header update
    headers = df.columns.tolist()

    city_titles = {
        "bangalore": "Bangalore Vehicle Status",
        "chennai": "Chennai Vehicle Status",
        "hyderabad": "Hyderabad Vehicle Status",
        "combined three cities": "Three Cities Vehicle Status"
    }

    key = title.replace("Vehicle Status", "").strip().lower()

    if len(headers) > 0:
        headers[0] = city_titles.get(key, title)
        df.columns = headers

    # ✅ FIX 1: Add spacing ONLY to vehicle header columns (not first column)
    header_html = "".join(
        f"<th>{h}</th>" if i == 0 else f"<th>\u2002\u2002{h}\u2002\u2002</th>"
        for i, h in enumerate(df.columns)
    )

    rows_html = ""

    # ✅ FIX 2: avoid crash (i is string index sometimes)
    for idx, (i, row) in enumerate(df.iterrows()):

        row_values = row.values.tolist()
        row_str = " ".join(str(v).lower() for v in row_values)

        # 🎯 Row styling logic
        if "total" in row_str:
            row_class = "total-row"
        elif idx % 2 == 0:
            row_class = "alt-row"
        else:
            row_class = ""

        # keep your existing EM SPACE logic for first column
        cells = ""
        for j, v in enumerate(row_values):
            if j == 0:
                v = f"  {v}  "   # EM SPACE
            cells += f"<td>{v}</td>"

        rows_html += f"<tr class='{row_class}'>{cells}</tr>"

    html = f"""
    <html>
    <head>
    <style>
    body {{
        font-family: 'Inter', Arial, sans-serif;
        margin: 0;
        padding: 0;
        background: white;
    }}

    table {{
        border-collapse: collapse;
        font-size: 14px;
        margin: 0;
    }}

    th {{
        background: #006400;
        color: white;
        font-weight: 600;
        padding: 10px;
        border: 1px solid #ddd;
        text-align: center;
    }}

    td {{
        padding: 10px;
        border: 1px solid #ddd;
        text-align: center;
    }}

    td:first-child {{
        padding-left: 30px;
        padding-right: 30px;
        text-align: left;
        text-align: center
    }}

    .alt-row {{
        background: #f9fafb;
    }}

    .total-row td {{
        background: #FFD700;
        font-weight: 700;
        color: black;
    }}

    </style>
    </head>

    <body>

    <table>
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>

    </body>
    </html>
    """

    return html