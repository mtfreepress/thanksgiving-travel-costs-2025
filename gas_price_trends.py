

from __future__ import annotations

import json
import csv
import re
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple

# notes:
# - "Week before" = the 7 days immediately before Thanksgiving.
# - "Week after" = the 7 days immediately after Thanksgiving.

THANKSGIVING: Dict[int, date] = {
	2020: date(2020, 11, 26),
	2021: date(2021, 11, 25),
	2022: date(2022, 11, 24),
	2023: date(2023, 11, 23),
	2024: date(2024, 11, 28),
}

# inflation factors to convert amounts in year -> 2025 Q2 dollars
INFLATION_FACTORS: Dict[int, float] = {
    2020: 1.2352,
    2021: 1.1578,
    2022: 1.081,
    2023: 1.0471,
    2024: 1.0191,
}


def parse_us_list_entries(data: List[dict]) -> List[Tuple[date, float]]:
	"""Extract (date, price) tuples from the JSON top-level structure's USList sections."""
	entries: List[Tuple[date, float]] = []
	if not isinstance(data, list):
		return entries
	for block in data:
		uslist = block.get("USList") or []
		for item in uslist:
			dt_str = item.get("datetime")
			price = item.get("price")
			if dt_str is None or price is None:
				continue
			try:
				d = datetime.strptime(dt_str, "%m/%d/%Y").date()
			except Exception:
				# try ISO fallback
				try:
					d = datetime.fromisoformat(dt_str).date()
				except Exception:
					continue
			try:
				price_f = float(price)
			except Exception:
				continue
			entries.append((d, price_f))
	return entries


def avg(values: List[float]) -> float:
	return sum(values) / len(values) if values else float('nan')


def process_file(json_path: Path, out_dir: Path) -> None:
	# derive city name: remove trailing '-gas' from stem if present
	city = re.sub(r"-gas$", "", json_path.stem)
	out_dir.mkdir(parents=True, exist_ok=True)
	out_path = out_dir / f"{city}.csv"

	with json_path.open("r", encoding="utf-8") as fh:
		data = json.load(fh)

	entries = parse_us_list_entries(data)
	# index by date for quick lookup; allow multiple prices per date
	by_date: Dict[date, List[float]] = {}
	for d, p in entries:
		by_date.setdefault(d, []).append(p)

	# compute averages and store keyed by (year, time)
	results: Dict[Tuple[int, str], float] = {}
	years = sorted(THANKSGIVING.keys())
	for y in years:
		td = THANKSGIVING[y]
		before_dates = [td - timedelta(days=d) for d in range(1, 8)]
		after_dates = [td + timedelta(days=d) for d in range(1, 8)]

		before_prices: List[float] = []
		after_prices: List[float] = []
		for d in before_dates:
			if d in by_date and d.year == y:
				before_prices.extend(by_date[d])
		for d in after_dates:
			if d in by_date and d.year == y:
				after_prices.extend(by_date[d])

		b_avg = avg(before_prices)
		a_avg = avg(after_prices)
		# store numeric values (may be NaN)
		results[(y, "before")] = b_avg
		results[(y, "after")] = a_avg

	# prepare rows with extra computed columns
	rows: List[List[str]] = []
	for y in years:
		for t in ("before", "after"):
			price = results.get((y, t))
			# formatted average price
			avg_str = f"{price:.2f}" if (price == price) else ""

			# YoY: compare to previous year same time (no percent sign in value)
			prev = results.get((y - 1, t))
			if prev is not None and prev == prev and price == price and prev != 0:
				yoy = (price - prev) / prev * 100.0
				yoy_str = f"{yoy:.2f}"
			else:
				yoy_str = ""

			# Since2020: compare to 2020 same time (no percent sign in value)
			base2020 = results.get((2020, t))
			if base2020 is not None and base2020 == base2020 and price == price and base2020 != 0:
				since2020 = (price - base2020) / base2020 * 100.0
				since2020_str = f"{since2020:.2f}"
			else:
				since2020_str = ""

			# Q2InflationAdj2025: multiply by inflation factor for year
			factor = INFLATION_FACTORS.get(y)
			if factor is not None and price == price:
				adj = price * factor
				adj_str = f"{adj:.2f}"
			else:
				adj_str = ""

			# inflation-adjusted percent changes
			# YoY inflation-adjusted: compare adj this year to adj previous year
			prev_price = results.get((y - 1, t))
			prev_factor = INFLATION_FACTORS.get(y - 1)
			if prev_price is not None and prev_price == prev_price and prev_factor is not None and factor is not None and prev_price != 0:
				adj_prev = prev_price * prev_factor
				adj_this = price * factor if price == price else float('nan')
				if adj_prev != 0 and adj_this == adj_this:
					yoy_infl = (adj_this - adj_prev) / adj_prev * 100.0
					yoy_infl_str = f"{yoy_infl:.2f}"
				else:
					yoy_infl_str = ""
			else:
				yoy_infl_str = ""

			# Since2020 inflation-adjusted: compare adj this year to adj 2020
			base2020_price = results.get((2020, t))
			base2020_factor = INFLATION_FACTORS.get(2020)
			if base2020_price is not None and base2020_price == base2020_price and base2020_factor is not None and factor is not None and base2020_price != 0:
				adj_2020 = base2020_price * base2020_factor
				adj_this = price * factor if price == price else float('nan')
				if adj_2020 != 0 and adj_this == adj_this:
					since2020_infl = (adj_this - adj_2020) / adj_2020 * 100.0
					since2020_infl_str = f"{since2020_infl:.2f}"
				else:
					since2020_infl_str = ""
			else:
				since2020_infl_str = ""

			rows.append([str(y), t, avg_str, yoy_str, since2020_str, adj_str, yoy_infl_str, since2020_infl_str])

	# write CSV
	with out_path.open("w", newline='') as csvf:
		writer = csv.writer(csvf)
		writer.writerow([
			"year",
			"time",
			"averagePrice",
			"%changeYoY",
			"%changeSince2020",
			"Q2InflationAdj2025",
			"%changeYoYInflationAdj",
			"%changeSince2020InflationAdj",
		])
		for r in rows:
			writer.writerow(r)

	print(f"Wrote: {out_path}")


def main(input_dir: Path | None = None, output_dir: Path | None = None) -> None:
	base = Path(__file__).resolve().parent
	input_dir = (base / "gas-data") if input_dir is None else Path(input_dir)
	output_dir = (base / "gas-analysis") if output_dir is None else Path(output_dir)

	json_files = sorted(input_dir.glob("*.json"))
	if not json_files:
		print(f"No JSON files found in {input_dir}")
		return

	for jf in json_files:
		try:
			process_file(jf, output_dir)
		except Exception as e:
			print(f"Error processing {jf}: {e}")


if __name__ == "__main__":
	main()

