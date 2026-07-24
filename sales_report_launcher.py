"""
Sales Report Generator — designed to be run via a Domino Launcher.

Domino launcher command should be configured as:
    python sales_report_launcher.py ${start_date} ${end_date} ${region}

Arguments (in order):
    1. start_date  -> Date input control (format: YYYY-MM-DD)
    2. end_date    -> Date input control (format: YYYY-MM-DD)
    3. region      -> Select input control (e.g. North, South, East, West, All)

Output:
    Writes email.html in the working directory. Domino automatically uses
    email.html as the body of the notification email sent to whoever ran
    the launcher, and also shows it in the Job results view.
"""

import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # no display needed on a Domino executor
import matplotlib.pyplot as plt


def load_sample_sales_data():
    """Stand-in for a real data source (DB, warehouse, Domino Dataset, etc.)"""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2025-01-01", "2026-07-01", freq="D")
    regions = ["North", "South", "East", "West"]
    rows = []
    for d in dates:
        for r in regions:
            rows.append({
                "date": d,
                "region": r,
                "revenue": max(0, rng.normal(1000, 250))
            })
    return pd.DataFrame(rows)


def main():
    if len(sys.argv) < 4:
        print("Usage: sales_report_launcher.py <start_date> <end_date> <region>")
        sys.exit(1)

    start_date, end_date, region = sys.argv[1], sys.argv[2], sys.argv[3]

    df = load_sample_sales_data()
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    if region != "All":
        df = df[df["region"] == region]

    total_revenue = df["revenue"].sum()
    avg_daily = df.groupby("date")["revenue"].sum().mean()

    # Chart: daily revenue trend
    daily = df.groupby("date")["revenue"].sum()
    plt.figure(figsize=(8, 4))
    daily.plot(kind="line")
    plt.title(f"Daily Revenue — {region} ({start_date} to {end_date})")
    plt.xlabel("Date")
    plt.ylabel("Revenue ($)")
    plt.tight_layout()
    plt.savefig("revenue_chart.png")

    # Build the HTML email/report body
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Sales Report — {region}</h2>
        <p><b>Period:</b> {start_date} to {end_date}</p>
        <p><b>Total Revenue:</b> ${total_revenue:,.2f}</p>
        <p><b>Average Daily Revenue:</b> ${avg_daily:,.2f}</p>
        <img src="revenue_chart.png" width="600"/>
        <p style="color:gray; font-size:12px;">
            Generated automatically by a Domino Launcher.
        </p>
    </body>
    </html>
    """

    with open("email.html", "w") as f:
        f.write(html)

    print("Report generated: email.html + revenue_chart.png")


if __name__ == "__main__":
    main()
