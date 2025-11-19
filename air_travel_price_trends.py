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
            # detect national average rows where airport or city contains 'National Average'
            airport_label = (r.get("airport") or "").strip()
            if (city == "" or code == "") and (airport_label.lower() == "national average" or city.lower() == "national average"):
                # synthesize a national-average record (set airportCode if missing)
                r_parsed = {
                    "year": int(r.get("year", "0")) if (r.get("year") or "").strip() else 0,
                    "airportCode": code if code else "NATIONAL",
                    "City": "National Average",
                    "averageFare": safe_float(r.get("averageFare")),
                    "2025Q2InflationAdjFare": safe_float(r.get("2025Q2InflationAdjFare")),
                }
                rows.append(r_parsed)
                continue
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


def write_aggregate(rows: List[Dict[str, Any]], out_dir: Path) -> None:
    """Write aggregate CSVs for big-6 and national average.

    big-6: Bozeman, Missoula, Billings, Kalispell, Great Falls, Helena
    """
    # place aggregates under `airfare-analysis/aggregate`
    out_base = out_dir.parent / "aggregate"
    out_base.mkdir(parents=True, exist_ok=True)

    # convenience index by (city, year)
    by_city_year: Dict[str, Dict[int, Dict[str, Any]]] = {}
    cities = set()
    for r in rows:
        city = r["City"]
        year = r["year"]
        cities.add(city)
        by_city_year.setdefault(city, {})[year] = r

    def compute_group_avg(group_cities: List[str]) -> Dict[int, Dict[str, Optional[float]]]:
        # returns mapping year -> {averageFare: x, adjFare: y}
        years = set()
        for c in group_cities:
            years.update(by_city_year.get(c, {}).keys())
        years = sorted(years)
        out: Dict[int, Dict[str, Optional[float]]] = {}
        for y in years:
            fares: List[float] = []
            adjs: List[float] = []
            for c in group_cities:
                rec = by_city_year.get(c, {}).get(y)
                if rec:
                    if rec.get("averageFare") is not None:
                        fares.append(rec.get("averageFare"))
                    if rec.get("2025Q2InflationAdjFare") is not None:
                        adjs.append(rec.get("2025Q2InflationAdjFare"))
            avg_fare = sum(fares) / len(fares) if fares else None
            avg_adj = sum(adjs) / len(adjs) if adjs else None
            out[y] = {"averageFare": avg_fare, "adjFare": avg_adj}
        return out

    big6 = ["Bozeman", "Missoula", "Billings", "Kalispell", "Great Falls", "Helena"]
    big6_map = compute_group_avg(big6)

    # write big-6 file
    big6_path = out_base / "big-6-analysis.csv"
    with big6_path.open("w", newline="", encoding="utf-8") as fh:
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
        years = sorted(big6_map.keys())
        for y in years:
            avg_fare = big6_map[y]["averageFare"]
            adj_fare = big6_map[y]["adjFare"]

            # YoY
            yoy = ""
            if (y - 1) in big6_map and avg_fare is not None and big6_map[y - 1]["averageFare"] not in (None, 0):
                prev = big6_map[y - 1]["averageFare"]
                yoy = f"{(avg_fare - prev) / prev * 100.0:.2f}"

            # since2015
            since2015 = ""
            if 2015 in big6_map and avg_fare is not None and big6_map[2015]["averageFare"] not in (None, 0):
                base = big6_map[2015]["averageFare"]
                since2015 = f"{(avg_fare - base) / base * 100.0:.2f}"

            # inflation-adjusted YoY / since2015
            yoy_infl = ""
            since2015_infl = ""
            if (y - 1) in big6_map and adj_fare is not None and big6_map[y - 1]["adjFare"] not in (None, 0):
                prev_adj = big6_map[y - 1]["adjFare"]
                yoy_infl = f"{(adj_fare - prev_adj) / prev_adj * 100.0:.2f}"
            if 2015 in big6_map and adj_fare is not None and big6_map[2015]["adjFare"] not in (None, 0):
                base_adj = big6_map[2015]["adjFare"]
                since2015_infl = f"{(adj_fare - base_adj) / base_adj * 100.0:.2f}"

            writer.writerow([
                str(y),
                "BIG6",
                "Big 6 (Bozeman,Missoula,Billings,Kalispell,Great Falls,Helena)",
                f"{avg_fare:.2f}" if avg_fare is not None else "",
                yoy,
                since2015,
                f"{adj_fare:.2f}" if adj_fare is not None else "",
                yoy_infl,
                since2015_infl,
            ])

    print(f"Wrote: {big6_path}")


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
                "%ChangeSince2015",
                "2025Q2InflationAdjFare",
                "%changeYoYInflationAdj",
                "%changeSince2015InflationAdj",
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

                # since 2015 percent change
                since2015_str = ""
                base2015 = recs_by_year.get(2015)
                if base2015 and avg_fare is not None and base2015.get("averageFare") not in (None, 0):
                    base_avg = base2015.get("averageFare")
                    since2015 = (avg_fare - base_avg) / base_avg * 100.0
                    since2015_str = f"{since2015:.2f}"

                # inflation-adjusted YoY and since-2015 use provided adj_fare when available
                yoy_infl_str = ""
                since2015_infl_str = ""
                if prev and adj_fare is not None and prev.get("2025Q2InflationAdjFare") not in (None, 0):
                    prev_adj = prev.get("2025Q2InflationAdjFare")
                    yoy_infl = (adj_fare - prev_adj) / prev_adj * 100.0
                    yoy_infl_str = f"{yoy_infl:.2f}"
                if base2015 and adj_fare is not None and base2015.get("2025Q2InflationAdjFare") not in (None, 0):
                    base_adj = base2015.get("2025Q2InflationAdjFare")
                    since2015_infl = (adj_fare - base_adj) / base_adj * 100.0
                    since2015_infl_str = f"{since2015_infl:.2f}"

                writer.writerow([
                    str(y),
                    code,
                    city,
                    f"{avg_fare:.2f}" if avg_fare is not None else "",
                    yoy_str,
                    since2015_str,
                    f"{adj_fare:.2f}" if adj_fare is not None else "",
                    yoy_infl_str,
                    since2015_infl_str,
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
    # also write aggregate files (big-6 and national average)
    write_aggregate(rows, OUT_DIR)


if __name__ == "__main__":
    main()
