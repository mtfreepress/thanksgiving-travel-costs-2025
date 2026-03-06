import json
import csv
from datetime import datetime, timedelta
from pathlib import Path


INPUT = Path("new-gas-prices/montana-gas-data.json")
OUT_DIR = Path("price-increases")


def load_uslist(path: Path):
    data = json.loads(path.read_text())
    if not data:
        return []
    us = data[0].get("USList", [])
    return us


# define date format
def to_date(s: str):
    return datetime.strptime(s, "%m/%d/%Y").date()


def compute_single_day(uslist):
    rows = []
    for a, b in zip(uslist, uslist[1:]):
        start_date = a["datetime"]
        end_date = b["datetime"]
        start_price = float(a["price"])
        end_price = float(b["price"])
        inc = end_price - start_price
        pct = round((inc / start_price) * 100) if start_price != 0 else 0
        rows.append({
            "startDate": start_date,
            "endDate": end_date,
            "startPrice": start_price,
            "endPrice": end_price,
            "increase": inc,
            "pctIncrease": int(pct),
        })
    return rows


def compute_weekly(uslist):
    date_map = {}
    orig_map = {}
    for e in uslist:
        ds = to_date(e["datetime"])
        date_map[ds] = float(e["price"])
        orig_map[ds] = e["datetime"]

    rows = []
    for ds in sorted(date_map):
        target = ds + timedelta(days=7)
        if target in date_map:
            start_price = date_map[ds]
            end_price = date_map[target]
            inc = end_price - start_price
            pct = round((inc / start_price) * 100) if start_price != 0 else 0
            rows.append({
                "startDate": orig_map[ds],
                "endDate": orig_map[target],
                "startPrice": start_price,
                "endPrice": end_price,
                "increase": inc,
                "pctIncrease": int(pct),
            })
    return rows


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["startDate", "endDate", "startPrice", "endPrice", "increase", "pctIncrease"])
        for r in rows:
            writer.writerow([
                r["startDate"],
                r["endDate"],
                f"{r['startPrice']:.3f}",
                f"{r['endPrice']:.3f}",
                f"{r['increase']:.3f}",
                r["pctIncrease"],
            ])


def main():
    uslist = load_uslist(INPUT)
    if not uslist:
        print("No USList data found in", INPUT)
        return

    single = compute_single_day(uslist)
    week = compute_weekly(uslist)

    single_sorted = sorted(single, key=lambda r: abs(r["increase"]), reverse=True)
    week_sorted = sorted(week, key=lambda r: abs(r["increase"]), reverse=True)

    write_csv(OUT_DIR / "montana-single-day.csv", single_sorted)
    write_csv(OUT_DIR / "montana-week.csv", week_sorted)

    print("Wrote:", OUT_DIR / "montana-single-day.csv")
    print("Wrote:", OUT_DIR / "montana-week.csv")


if __name__ == "__main__":
    main()
