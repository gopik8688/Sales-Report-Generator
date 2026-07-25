"""
Sales Report Generator — designed to be run via a Domino Launcher.

Domino launcher command should be configured as:
    sales_report_launcher.py ${start_date} ${end_date} ${region}

Arguments (in order):
    1. start_date  -> Date input control
    2. end_date    -> Date input control
    3. region      -> Select input control (e.g. North, South, East, West, All)

Output:
    Writes report.pdf (and revenue_chart.png) to /mnt/artifacts, so Domino
    automatically surfaces them as downloadable files on the Job's Results tab.

Data source:
    Reads sales data from a Domino Dataset CSV at DATASET_PATH (see below).
    If that file isn't found, falls back to fabricated sample data so the
    launcher stays demoable before the real Dataset is wired up.
"""

import os
import re
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # no display needed on a Domino executor
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors

# Domino only auto-saves job outputs written to /mnt/artifacts.
OUTPUT_DIR = "/mnt/artifacts"

# Path to the real sales data file inside a mounted Domino Dataset.
# Domino Datasets are mounted read-only at /domino/datasets/<data-plane>/<DatasetName>/...
# Update this to match your project's actual Dataset name and file.
DATASET_PATH = "/mnt/data/Sales_Report_Generator/sales.csv"

# Expected columns in the CSV: date, region, revenue
# - date:    parseable date string (e.g. YYYY-MM-DD)
# - region:  one of North / South / East / West (or whatever your Select options are)
# - revenue: numeric


def parse_domino_date(value):
    """
    Domino Date launcher parameters arrive as a JS Date.toString() string, e.g.:
        'Sun Mar 01 2026 00:00:00 GMT+0530 (India Standard Time)'
    instead of a plain 'YYYY-MM-DD' string. Strip the trailing
    '(Zone Name)' portion (which pandas/dateutil can't parse) before
    converting to a pandas Timestamp, then drop timezone info so it can
    be compared against the naive dates in our sample dataframe.
    """
    cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", value.strip())
    ts = pd.to_datetime(cleaned)
    if ts.tzinfo is not None:
        ts = ts.tz_localize(None)
    return ts


def load_sales_data():
    """
    Load real sales data from a Domino Dataset CSV file.

    Falls back to fabricated sample data (with a warning) if the Dataset
    file isn't found yet — this keeps the launcher demoable before the
    real Dataset is wired up, and makes the missing-file case obvious in
    the job logs rather than failing silently or crashing.
    """
    if os.path.exists(DATASET_PATH):
        df = pd.read_csv(DATASET_PATH, parse_dates=["date"])
        required_cols = {"date", "region", "revenue"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(
                f"Dataset at {DATASET_PATH} is missing required columns: {missing}"
            )
        return df

    print(
        f"WARNING: Dataset file not found at {DATASET_PATH}. "
        "Falling back to fabricated sample data. Update DATASET_PATH "
        "once the real Domino Dataset is mounted to this project."
    )
    return load_sample_sales_data()


def load_sample_sales_data():
    """Fallback stand-in used only when the real Dataset file isn't available."""
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


def build_pdf_report(pdf_path, chart_path, region, start_date_display,
                      end_date_display, total_revenue, avg_daily, best_day, worst_day):
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Sales Report", styles["Title"]))
    story.append(Paragraph(f"Region: {region}", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Period: {start_date_display} to {end_date_display}", styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    summary_data = [
        ["Metric", "Value"],
        ["Total Revenue", f"${total_revenue:,.2f}"],
        ["Average Daily Revenue", f"${avg_daily:,.2f}"],
        ["Best Day", f"{best_day[0]} (${best_day[1]:,.2f})"],
        ["Worst Day", f"{worst_day[0]} (${worst_day[1]:,.2f})"],
    ]
    table = Table(summary_data, colWidths=[2.5 * inch, 2.5 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4B4BE0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Daily Revenue Trend", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Image(chart_path, width=6.5 * inch, height=3.25 * inch))
    story.append(Spacer(1, 20))

    story.append(Paragraph(
        "Generated automatically by a Domino Launcher.", styles["Italic"]
    ))

    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                             topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    doc.build(story)


def main():
    if len(sys.argv) < 4:
        print("Usage: sales_report_launcher.py <start_date> <end_date> <region>")
        sys.exit(1)

    start_date_raw, end_date_raw, region = sys.argv[1], sys.argv[2], sys.argv[3]
    start_date = parse_domino_date(start_date_raw)
    end_date = parse_domino_date(end_date_raw)

    df = load_sales_data()
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    if region != "All":
        df = df[df["region"] == region]

    daily = df.groupby("date")["revenue"].sum()
    total_revenue = daily.sum()
    avg_daily = daily.mean()
    best_day = (daily.idxmax().strftime("%Y-%m-%d"), daily.max())
    worst_day = (daily.idxmin().strftime("%Y-%m-%d"), daily.min())
    start_date_display = start_date.strftime("%Y-%m-%d")
    end_date_display = end_date.strftime("%Y-%m-%d")

    # Chart: daily revenue trend
    plt.figure(figsize=(8, 4))
    daily.plot(kind="line")
    plt.title(f"Daily Revenue — {region} ({start_date_display} to {end_date_display})")
    plt.xlabel("Date")
    plt.ylabel("Revenue ($)")
    plt.tight_layout()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chart_path = os.path.join(OUTPUT_DIR, "revenue_chart.png")
    plt.savefig(chart_path)
    plt.close()

    pdf_path = os.path.join(OUTPUT_DIR, "report.pdf")
    build_pdf_report(
        pdf_path, chart_path, region, start_date_display, end_date_display,
        total_revenue, avg_daily, best_day, worst_day,
    )

    print(f"Report generated: {pdf_path} + {chart_path}")


if __name__ == "__main__":
    main()