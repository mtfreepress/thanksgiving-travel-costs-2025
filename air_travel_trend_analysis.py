from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Dict, Optional


BY_AIRPORT_DIR = Path("airfare-analysis/by-airport")
AGGREGATE_FILE = Path("airfare-analysis/aggregate/big-6-analysis.csv")

YEAR_YOY_DIR = Path("airfare-analysis/year-over-year")
YEAR_SINCE_DIR = Path("airfare-analysis/since-2015")

# Entities to include (big 6 cities) - filenames created earlier
BIG6_FILES = [
    "bozeman-analysis.csv",
    "missoula-analysis.csv",
    "billings-analysis.csv",
    "kalispell-analysis.csv",
    "great-falls-analysis.csv",
    "helena-analysis.csv",
]

# include national average (present under by-airport) and the aggregate file
NATIONAL_FILE = "national-average-analysis.csv"

YEARS = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            # normalize keys and keep as strings
            rows.append({k: (v or "").strip() for k, v in r.items()})
    return rows


def float_or_none(s: str) -> Optional[float]:
    if s is None or s == "":
        return None
    try:
        # strip possible percent sign
        return float(s.replace('%', ''))
    except Exception:
        return None


def collect_entities() -> List[Dict[str, str]]:
    """Collect rows for all entities to include (big6 files, national, aggregate)."""
    collected: List[Dict[str, str]] = []

    # read big6 per-airport files
    for fname in BIG6_FILES:
        p = BY_AIRPORT_DIR / fname
        collected.extend(read_csv_rows(p))

    # national average (by-airport)
    collected.extend(read_csv_rows(BY_AIRPORT_DIR / NATIONAL_FILE))

    # aggregate big-6
    collected.extend(read_csv_rows(AGGREGATE_FILE))

    return collected


def make_dirs() -> None:
    YEAR_YOY_DIR.mkdir(parents=True, exist_ok=True)
    YEAR_SINCE_DIR.mkdir(parents=True, exist_ok=True)


def write_sorted_for_year(rows: List[Dict[str, str]], year: int) -> None:
    # filter rows for this year
    rows_y = [r for r in rows if r.get("year") and int(r.get("year")) == year]

    # prepare YoY file sorted by %changeYoYInflationAdj (descending)
    def key_yoy(r: Dict[str, str]) -> float:
        v = float_or_none(r.get("%changeYoYInflationAdj", ""))
        return v if v is not None else float("-inf")

    rows_y_yoy_sorted = sorted(rows_y, key=key_yoy, reverse=True)

    out_yoy = YEAR_YOY_DIR / f"{year}-YoY-change.csv"
    if rows_y_yoy_sorted:
        with out_yoy.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            header = [
                "year",
                "airportCode",
                "City",
                "averageFare",
                "%YoYChange",
                "%ChangeSince2015",
                "2025Q2InflationAdjFare",
                "%changeYoYInflationAdj",
                "%changeSince2015InflationAdj",
            ]
            writer.writerow(header)
            for r in rows_y_yoy_sorted:
                writer.writerow([
                    r.get("year", ""),
                    r.get("airportCode", ""),
                    r.get("City", ""),
                    r.get("averageFare", ""),
                    r.get("%YoYChange", ""),
                    r.get("%ChangeSince2015", ""),
                    r.get("2025Q2InflationAdjFare", ""),
                    r.get("%changeYoYInflationAdj", ""),
                    r.get("%changeSince2015InflationAdj", ""),
                ])
    print(f"Wrote: {out_yoy}")

    # prepare since-2015 file sorted by %changeSince2015InflationAdj (descending)
    def key_since(r: Dict[str, str]) -> float:
        v = float_or_none(r.get("%changeSince2015InflationAdj", ""))
        return v if v is not None else float("-inf")

    rows_y_since_sorted = sorted(rows_y, key=key_since, reverse=True)
    out_since = YEAR_SINCE_DIR / f"{year}-since-2015-change.csv"
    if rows_y_since_sorted:
        with out_since.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            header = [
                "year",
                "airportCode",
                "City",
                "averageFare",
                "%YoYChange",
                "%ChangeSince2015",
                "2025Q2InflationAdjFare",
                "%changeYoYInflationAdj",
                "%changeSince2015InflationAdj",
            ]
            writer.writerow(header)
            for r in rows_y_since_sorted:
                writer.writerow([
                    r.get("year", ""),
                    r.get("airportCode", ""),
                    r.get("City", ""),
                    r.get("averageFare", ""),
                    r.get("%YoYChange", ""),
                    r.get("%ChangeSince2015", ""),
                    r.get("2025Q2InflationAdjFare", ""),
                    r.get("%changeYoYInflationAdj", ""),
                    r.get("%changeSince2015InflationAdj", ""),
                ])
    print(f"Wrote: {out_since}")


def main() -> None:
    make_dirs()
    rows = collect_entities()
    if not rows:
        print("No rows found; ensure `airfare-analysis/by-airport` and aggregate file exist")
        return

    for y in YEARS:
        write_sorted_for_year(rows, y)


if __name__ == "__main__":
    main()
