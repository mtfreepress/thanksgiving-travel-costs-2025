from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Any, Optional


INPUT_CSV = Path("airfare-data/montana-air-travel-Q4-price.csv")
OUT_DIR = Path("airfare-analysis/by-airport")


def safe_float(x: Any) -> Optional[float]:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


def slug_city(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


def read_input(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            # skip rows with no city or airportCode (National Average rows)
            city = (r.get("city") or "").strip()
            code = (r.get("aiportCode") or r.get("airportCode") or "").strip()
            if city == "" or code == "":
                continue
            # normalize keys
            r_parsed = {
                "year": int(r.get("year", "0")) if (r.get("year") or "").strip() else 0,
                "airportCode": code,
                "City": city,
                "averageFare": safe_float(r.get("averageFare")),
                "2025Q2InflationAdjFare": safe_float(r.get("2025Q2InflationAdjFare")),
            }
            rows.append(r_parsed)
    return rows


def write_city_files(rows: List[Dict[str, Any]], out_dir: Path) -> None:
    # group by city + airportCode
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        key = f"{r['City']}|{r['airportCode']}"
        grouped.setdefault(key, []).append(r)

    out_dir.mkdir(parents=True, exist_ok=True)
    for key, recs in grouped.items():
        city, code = key.split("|")
        filename = f"{slug_city(city)}-analysis.csv"
        out_path = out_dir / filename

        # index by year
        recs_by_year: Dict[int, Dict[str, Any]] = {r["year"]: r for r in recs}
        years = sorted(recs_by_year.keys())

        with out_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow([
                "year",
                "airportCode",
                "City",
                "averageFare",
                "%YoYChange",
                "%ChangeSince2020",
                "2025Q2InflationAdjFare",
                "%changeYoYInflationAdj",
                "%changeSince2020InflationAdj",
            ])

            for y in years:
                rec = recs_by_year[y]
                avg_fare = rec.get("averageFare")
                adj_fare = rec.get("2025Q2InflationAdjFare")

                # compute YoY percent change (no % sign in value)
                prev = recs_by_year.get(y - 1)
                yoy_str = ""
                if prev and avg_fare is not None and prev.get("averageFare") not in (None, 0):
                    prev_avg = prev.get("averageFare")
                    yoy = (avg_fare - prev_avg) / prev_avg * 100.0
                    yoy_str = f"{yoy:.2f}"

                # since 2020 percent change
                since2020_str = ""
                base2020 = recs_by_year.get(2020)
                if base2020 and avg_fare is not None and base2020.get("averageFare") not in (None, 0):
                    base_avg = base2020.get("averageFare")
                    since2020 = (avg_fare - base_avg) / base_avg * 100.0
                    since2020_str = f"{since2020:.2f}"

                # inflation-adjusted YoY and since-2020 use provided adj_fare when available
                yoy_infl_str = ""
                since2020_infl_str = ""
                if prev and adj_fare is not None and prev.get("2025Q2InflationAdjFare") not in (None, 0):
                    prev_adj = prev.get("2025Q2InflationAdjFare")
                    yoy_infl = (adj_fare - prev_adj) / prev_adj * 100.0
                    yoy_infl_str = f"{yoy_infl:.2f}"
                if base2020 and adj_fare is not None and base2020.get("2025Q2InflationAdjFare") not in (None, 0):
                    base_adj = base2020.get("2025Q2InflationAdjFare")
                    since2020_infl = (adj_fare - base_adj) / base_adj * 100.0
                    since2020_infl_str = f"{since2020_infl:.2f}"

                writer.writerow([
                    str(y),
                    code,
                    city,
                    f"{avg_fare:.2f}" if avg_fare is not None else "",
                    yoy_str,
                    since2020_str,
                    f"{adj_fare:.2f}" if adj_fare is not None else "",
                    yoy_infl_str,
                    since2020_infl_str,
                ])

        print(f"Wrote: {out_path}")


def main() -> None:
    if not INPUT_CSV.exists():
        print(f"Input CSV not found: {INPUT_CSV}")
        return
    rows = read_input(INPUT_CSV)
    if not rows:
        print("No valid rows found in input CSV")
        return
    write_city_files(rows, OUT_DIR)


if __name__ == "__main__":
    main()
