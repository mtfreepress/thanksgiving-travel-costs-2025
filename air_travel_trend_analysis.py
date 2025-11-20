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

    # also produce an all-years CSV combining since-2015 data (including 2015)
    write_all_years(rows)


def write_all_years(rows: List[Dict[str, str]]) -> None:
    out_path = Path("airfare-analysis/all-years.csv")
    # build mapping entity -> year -> record
    by_entity: Dict[str, Dict[int, Dict[str, str]]] = {}
    years_set = set()
    for r in rows:
        code = r.get("airportCode", "")
        city = r.get("City", "")
        key = f"{code}|{city}"
        y = int(r.get("year") or 0)
        years_set.add(y)
        by_entity.setdefault(key, {})[y] = r

    # ensure 2015 included
    years = sorted(years_set.union({2015}))

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "year",
            "airportCode",
            "City",
            "averageFare",
            "%YoYChange",
            "%ChangeSince2015",
            "2025Q2InflationAdjFare",
            "%changeYoYInflationAdj",
            "%changeSince2015InflationAdj",
        ])

        for key, recs in sorted(by_entity.items()):
            code, city = key.split("|", 1)
            # for each year in chronological order
            for y in years:
                rec = recs.get(y)
                avg = float_or_none(rec.get("averageFare")) if rec else None
                adj = float_or_none(rec.get("2025Q2InflationAdjFare")) if rec else None

                # YoY: compare to previous year if exists
                yoy = ""
                if y != 2015 and (y - 1) in recs and avg is not None:
                    prev_rec = recs.get(y - 1)
                    prev_avg = float_or_none(prev_rec.get("averageFare")) if prev_rec else None
                    if prev_avg not in (None, 0):
                        yoy = f"{(avg - prev_avg) / prev_avg * 100.0:.2f}"

                # since2015: compare to 2015 if present
                since2015 = ""
                base2015_rec = recs.get(2015)
                base2015 = float_or_none(base2015_rec.get("averageFare")) if base2015_rec else None
                if y != 2015 and base2015 not in (None, 0) and avg is not None:
                    since2015 = f"{(avg - base2015) / base2015 * 100.0:.2f}"

                # inflation-adjusted YoY and since2015
                yoy_infl = ""
                since2015_infl = ""
                if y != 2015 and (y - 1) in recs and adj is not None:
                    prev_adj = float_or_none(recs.get(y - 1).get("2025Q2InflationAdjFare"))
                    if prev_adj not in (None, 0):
                        yoy_infl = f"{(adj - prev_adj) / prev_adj * 100.0:.2f}"
                if y != 2015 and base2015_rec and adj is not None:
                    base_adj = float_or_none(base2015_rec.get("2025Q2InflationAdjFare"))
                    if base_adj not in (None, 0):
                        since2015_infl = f"{(adj - base_adj) / base_adj * 100.0:.2f}"

                writer.writerow([
                    str(y),
                    code,
                    city,
                    f"{avg:.2f}" if avg is not None else "",
                    yoy,
                    since2015,
                    f"{adj:.2f}" if adj is not None else "",
                    yoy_infl,
                    since2015_infl,
                ])

    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
