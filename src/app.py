"""Dash app to visualize national Complications and Deaths rates over time.

Reads the complications_and_deaths_national table (built by
data/extract_and_store_data.py) from data/care_compare_db_1 and lets the
user pick a measure from a dropdown to see its national rate trend.

Usage:
    python src/app.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "care_compare_db_1"
TABLE_NAME = "complications_and_deaths_national"


def load_data() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    df["period_midpoint"] = pd.to_datetime(df["period_midpoint"])
    return df


data = load_data()

measure_options = (
    data[["canonical_measure_id", "measure_label"]]
    .drop_duplicates()
    .sort_values("measure_label")
)
DROPDOWN_OPTIONS = [
    {"label": row.measure_label, "value": row.canonical_measure_id}
    for row in measure_options.itertuples()
]
DEFAULT_MEASURE = DROPDOWN_OPTIONS[0]["value"]

app = Dash(__name__)
app.title = "Care Compare: Complications and Deaths"

app.layout = html.Div(
    style={
        "fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif",
        "maxWidth": "900px",
        "margin": "40px auto",
        "padding": "0 20px",
    },
    children=[
        html.H1(
            "National Complications and Deaths Rates",
            style={"fontSize": "26px", "marginBottom": "4px"},
        ),
        html.P(
            "Select a measure to see how its national rate has changed across "
            "CMS reporting periods.",
            style={"color": "#555", "marginTop": "0"},
        ),
        dcc.Dropdown(
            id="measure-dropdown",
            options=DROPDOWN_OPTIONS,
            value=DEFAULT_MEASURE,
            clearable=False,
            style={"marginBottom": "24px"},
        ),
        dcc.Graph(id="measure-trend-graph"),
    ],
)


@app.callback(
    Output("measure-trend-graph", "figure"),
    Input("measure-dropdown", "value"),
)
def update_graph(canonical_measure_id: str):
    measure_data = data[data["canonical_measure_id"] == canonical_measure_id].sort_values(
        "period_midpoint"
    )
    measure_label = measure_data["measure_label"].iloc[0]

    fig = px.line(
        measure_data,
        x="period_midpoint",
        y="national_rate",
        markers=True,
        labels={"period_midpoint": "Reporting period", "national_rate": "National rate"},
        title=measure_label,
    )
    fig.update_traces(line_color="#2c6fbb", marker={"size": 8, "color": "#2c6fbb"})
    fig.update_layout(
        template="plotly_white",
        title_font_size=18,
        margin={"t": 60, "b": 40, "l": 60, "r": 20},
    )
    return fig


if __name__ == "__main__":
    app.run(debug=True, port=8000)
