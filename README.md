# Sales Report Generator — Domino Launcher

A self-serve Domino Launcher that lets non-technical users generate a sales
revenue report (with a trend chart) for a chosen date range and region —
no code or notebook access required.

## What this project demonstrates

This is a working reference example of the **Launcher** pattern in Domino:
exposing a parameterized script as a simple web form so business
stakeholders can trigger analysis on demand, with results tracked,
reproducible, and auditable like any other Domino job.

## Files

| File | Purpose |
|---|---|
| `sales_report_launcher.py` | The script the launcher runs. Takes `start_date`, `end_date`, and `region` as CLI args, filters a sample sales dataset, generates a revenue trend chart, and builds a downloadable PDF report. |
| `requirements.txt` | Python dependencies (`pandas`, `numpy`, `matplotlib`, `reportlab`) needed in the project's environment. |

## Setup

1. **Upload the script** — add `sales_report_launcher.py` to this project's **Code** section.
2. **Install dependencies** — add the contents of `requirements.txt` to the
   project's environment (Environments → Pip section) and rebuild the
   environment.
3. **Create the Launcher** — go to **Deployments → Launchers → New Launcher**
   and configure:

   **Command to run:**
   ```
   sales_report_launcher.py ${start_date} ${end_date} ${region}
   ```

   **Parameters:**

   | Name | Type | Config |
   |---|---|---|
   | `start_date` | Date | — |
   | `end_date` | Date | — |
   | `region` | Select | Allowed values: `North, South, East, West, All` |

4. **Save**, then **Run** with test inputs to confirm it works end to end.

## Outputs

The script writes both outputs to `/mnt/artifacts/` so Domino automatically
persists them as downloadable **Results** on the completed job:

- `revenue_chart.png` — daily revenue trend chart for the selected period/region
- `report.pdf` — a formatted PDF report with a summary table (total revenue,
  average daily revenue, best/worst day) and the embedded chart

Anyone who runs the launcher can open the job's Results tab and download
`report.pdf` directly — no email delivery required.

> **Note:** Only files written to `/mnt/artifacts` are automatically saved
> and shown in a job's Results tab — files written elsewhere (e.g. the
> working directory) will not appear there.

## Known gotcha: Date parameter format

Domino's **Date** input type does not pass a plain `YYYY-MM-DD` string to
the script. It passes a full JavaScript `Date.toString()` value, e.g.:

```
Sun Mar 01 2026 00:00:00 GMT+0530 (India Standard Time)
```

The script handles this via a `parse_domino_date()` helper that strips the
trailing timezone-name parenthetical and converts the result to a
timezone-naive `pandas.Timestamp`. Any future launcher script using a Date
parameter and pandas should apply the same handling, or comparisons against
a `datetime64` column will fail with a `DateParseError` /
`TypeError: Invalid comparison between dtype=datetime64[ns] and str`.

