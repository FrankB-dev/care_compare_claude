# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This repository currently contains only raw CMS Care Compare data and a README specifying what to build — no application code exists yet (no `src/` or `data/*.py` files). The README's "Primer" section (lines between `### Primer` and `### End Primer`) is the authoritative spec for this project. **Do not alter or rephrase the Primer section** — it is a fixed instruction set. Document your own approach, decisions, and progress in the "Claude Code documentation" section below the Primer instead.

## Goal

Build a local dash-plotly app that visualizes national complications-and-deaths data extracted from CMS Care Compare data files. Two files are required:

1. **`data/extract_and_store_data.py`** — ETL script that reads the national complications-and-deaths CSVs from each `data/<year>/` folder, cleans/validates them, and writes them into a SQLite database `care_compare_db_1` in a table named `complications_and_deaths_national`. New derived columns/features may be added if they'll help the visualization.
2. **`src/app.py`** — Dash app that reads `complications_and_deaths_national` from the SQLite db, offers a dropdown to select a measure, and plots that measure's national rate over time. The dropdown must remain visible/selectable after a graph is shown, and switching the selection should update the graph in place.

## Environment

A venv already exists at `.venv/` with the packages from `requirements.txt` installed (pandas, numpy, notebook, matplotlib, `plotly[express]`, dash). Use only these libraries — no other third-party dependencies.

```bash
source .venv/bin/activate
python data/extract_and_store_data.py   # build/refresh care_compare_db_1
python src/app.py                        # run the Dash app locally
```

There is no test suite, linter, or build step configured — don't invent commands for these.

## Data layout

`data/<year>/` folders exist for 2019–2026 (CMS Care Compare exports), each `.gitignore`'d in full — only code files committed directly under `data/` (not inside a year subfolder) are tracked by git. **2020 has no data files** (empty folder — a gap year to handle in the ETL).

The relevant national-level file per year is named inconsistently across years but has a stable schema:
- 2019: `Complications and Deaths - National.csv` (spaces)
- 2021+: `Complications_and_Deaths-National.csv` (underscores/hyphen)

Columns (consistent across years): `Measure ID`, `Measure Name`, `National Rate`, `Number of Hospitals Worse`, `Number of Hospitals Same`, `Number of Hospitals Better`, `Number of Hospitals Too Few`, `Footnote`, `Start Date`, `End Date`. Each year's file has a different `Start Date`/`End Date` reporting window — this is what makes the "national rate over time" trend meaningful across years. `Measure ID`/`Measure Name` sets shift somewhat between years (e.g. `Hybrid_HWM` only appears in later years), so the ETL should not assume a fixed measure list.

There are many other unrelated CSVs in each year's folder (HCAHPS, HAC, MSPB, etc.) — only the Complications-and-Deaths national file is in scope per the Primer.
