"""Extract national Complications and Deaths data from each year folder in
data/ and store it, cleaned and consolidated, in a SQLite database.

Usage:
    python data/extract_and_store_data.py

Produces data/care_compare_db_1 with a single table,
complications_and_deaths_national.
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "care_compare_db_1"
TABLE_NAME = "complications_and_deaths_national"

# The national Complications-and-Deaths file is named differently across
# report vintages but has a stable schema. Try each known spelling in turn.
NATIONAL_FILE_CANDIDATES = [
    "Complications_and_Deaths-National.csv",
    "Complications and Deaths - National.csv",
]

RAW_COLUMNS = {
    "Measure ID": "measure_id",
    "Measure Name": "measure_name",
    "National Rate": "national_rate",
    "Number of Hospitals Worse": "hospitals_worse",
    "Number of Hospitals Same": "hospitals_same",
    "Number of Hospitals Better": "hospitals_better",
    "Number of Hospitals Too Few": "hospitals_too_few",
    "Footnote": "footnote",
    "Start Date": "start_date",
    "End Date": "end_date",
}

NUMERIC_COLUMNS = [
    "national_rate",
    "hospitals_worse",
    "hospitals_same",
    "hospitals_better",
    "hospitals_too_few",
]


def find_year_folders() -> list[Path]:
    """Return data/<year> folders, sorted, for folders that look like years."""
    return sorted(
        (p for p in DATA_DIR.iterdir() if p.is_dir() and re.fullmatch(r"\d{4}", p.name)),
        key=lambda p: int(p.name),
    )


def find_national_file(year_folder: Path) -> Path | None:
    for name in NATIONAL_FILE_CANDIDATES:
        candidate = year_folder / name
        if candidate.exists():
            return candidate
    return None


def canonicalize_measure_id(raw_measure_id: str) -> str:
    """Normalize measure IDs that changed spelling across years.

    Older files use e.g. "PSI_10_POST_KIDNEY"; newer files use "PSI_10" for
    the same underlying measure. Reduce any PSI_<n>... ID to a zero-padded
    "PSI_<nn>" so the same measure can be tracked across years. Other IDs
    (COMP_HIP_KNEE, MORT_30_*, Hybrid_HWM, ...) have been stable and pass
    through unchanged.
    """
    match = re.match(r"^PSI_(\d+)", raw_measure_id)
    if match:
        return f"PSI_{int(match.group(1)):02d}"
    return raw_measure_id


def load_year(year_folder: Path) -> pd.DataFrame | None:
    source_file = find_national_file(year_folder)
    if source_file is None:
        print(f"  [{year_folder.name}] no national complications-and-deaths file found, skipping")
        return None

    df = pd.read_csv(source_file, dtype=str)
    missing = set(RAW_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{source_file} is missing expected columns: {missing}")

    df = df.rename(columns=RAW_COLUMNS)[list(RAW_COLUMNS.values())]
    df["source_year"] = int(year_folder.name)
    print(f"  [{year_folder.name}] {len(df)} rows from {source_file.name}")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in NUMERIC_COLUMNS:
        # CMS uses "Not Available" (usually alongside footnote 5, the
        # COVID-19 reporting exception) for suppressed values.
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["start_date"] = pd.to_datetime(df["start_date"], format="%m/%d/%Y")
    df["end_date"] = pd.to_datetime(df["end_date"], format="%m/%d/%Y")
    df["footnote"] = df["footnote"].replace("", pd.NA)

    df["canonical_measure_id"] = df["measure_id"].map(canonicalize_measure_id)

    # Denormalized, human-readable label for each canonical measure, taken
    # from its most recent year's wording, so a dropdown in the app can show
    # one consistent name per measure regardless of which year's row it's
    # displaying. Helps the visualization group/label measures consistently.
    latest_names = (
        df.sort_values("source_year")
        .groupby("canonical_measure_id")["measure_name"]
        .last()
        .rename("measure_label")
    )
    df = df.merge(latest_names, on="canonical_measure_id", how="left")

    # Midpoint of the reporting window, used as the x-axis point for a
    # measure's rate "over time" since each row covers a date range rather
    # than a single date.
    df["period_midpoint"] = df["start_date"] + (df["end_date"] - df["start_date"]) / 2

    df["start_date"] = df["start_date"].dt.strftime("%Y-%m-%d")
    df["end_date"] = df["end_date"].dt.strftime("%Y-%m-%d")
    df["period_midpoint"] = df["period_midpoint"].dt.strftime("%Y-%m-%d")

    column_order = [
        "source_year",
        "canonical_measure_id",
        "measure_label",
        "measure_id",
        "measure_name",
        "national_rate",
        "hospitals_worse",
        "hospitals_same",
        "hospitals_better",
        "hospitals_too_few",
        "footnote",
        "start_date",
        "end_date",
        "period_midpoint",
    ]
    return df[column_order].sort_values(["canonical_measure_id", "source_year"]).reset_index(drop=True)


def main() -> None:
    print("Scanning year folders under data/ ...")
    frames = []
    for year_folder in find_year_folders():
        df = load_year(year_folder)
        if df is not None:
            frames.append(df)

    if not frames:
        raise SystemExit("No national complications-and-deaths files were found under data/.")

    combined = clean(pd.concat(frames, ignore_index=True))

    with sqlite3.connect(DB_PATH) as conn:
        combined.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)

    print(f"Wrote {len(combined)} rows to {DB_PATH} (table: {TABLE_NAME})")


if __name__ == "__main__":
    main()
