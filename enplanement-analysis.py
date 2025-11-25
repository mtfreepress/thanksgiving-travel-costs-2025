from pathlib import Path
import csv
import sys


def read_enplanements(path: Path):
	with path.open(newline="", encoding="utf-8") as f:
		reader = csv.DictReader(f)
		rows = list(reader)
	return rows


def parse_year_columns(fieldnames):
	years = []
	for name in fieldnames:
		if name.endswith("Passenger") and name[:4].isdigit():
			years.append(int(name[:4]))
	years.sort()
	return years


def build_airport_data(rows, years):
	data = {}
	for r in rows:
		code = r.get("airportCode")
		if not code:
			continue
		entry = {
			"airportCode": code,
			"airportName": r.get("airportName", ""),
			"city": r.get("city", ""),
			"passengers": {}
		}
		for y in years:
			key = f"{y}Passenger"
			val = r.get(key, "")
			try:
				entry["passengers"][y] = int(val) if val != "" else None
			except ValueError:
				entry["passengers"][y] = None
		data[code] = entry
	return data


def format_pct(n):
	if n is None:
		return ""
	return f"{n:.2f}"


def safe_div(numer, denom):
	try:
		return (numer / denom) * 100.0
	except Exception:
		return None


def generate_by_airport(data, years, out_path: Path):
	out_path.parent.mkdir(parents=True, exist_ok=True)
	header = [
		"year",
		"passengeRank",
		"aiportCode",
		"airport",
		"city",
		"passengers",
		"changeYoY",
		"%changeYoy",
		"changeSince2015",
		"%changeSince2015",
		"changeSince2019",
		"%changeSince2019",
		"changeSince2020",
		"%changeSince2020",
	]

	with out_path.open("w", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)
		writer.writerow(header)

		for y in years:
			# build list of (code, passengers)
			recs = []
			for code, info in data.items():
				p = info["passengers"].get(y)
				recs.append((code, p))
			# sort by passengers desc (None treated as -inf)
			recs.sort(key=lambda x: (x[1] is not None, x[1]), reverse=True)

			# assign ranks
			rank = 0
			last_val = None
			for i, (code, p) in enumerate(recs, start=1):
				if p is None:
					# skip airports with no data for this year
					rank = i
				else:
					if p != last_val:
						rank = i
					last_val = p

				info = data[code]
				prev = info["passengers"].get(y - 1)
				base2015 = info["passengers"].get(years[0])

				change_yoy = None
				pct_yoy = None
				if p is not None and prev is not None:
					change_yoy = p - prev
					pct_yoy = safe_div(change_yoy, prev)

				change_2015 = None
				pct_2015 = None
				if p is not None and base2015 is not None:
					change_2015 = p - base2015
					pct_2015 = safe_div(change_2015, base2015)

				# since 2019 and 2020
				base2019 = info["passengers"].get(2019)
				change_2019 = None
				pct_2019 = None
				if p is not None and base2019 is not None:
					change_2019 = p - base2019
					pct_2019 = safe_div(change_2019, base2019)

				base2020 = info["passengers"].get(2020)
				change_2020 = None
				pct_2020 = None
				if p is not None and base2020 is not None:
					change_2020 = p - base2020
					pct_2020 = safe_div(change_2020, base2020)

				writer.writerow([
					y,
					rank,
					info["airportCode"],
					info["airportName"],
					info["city"],
					p if p is not None else "",
					change_yoy if change_yoy is not None else "",
					format_pct(pct_yoy) if pct_yoy is not None else "",
					change_2015 if change_2015 is not None else "",
					format_pct(pct_2015) if pct_2015 is not None else "",
					change_2019 if change_2019 is not None else "",
					format_pct(pct_2019) if pct_2019 is not None else "",
					change_2020 if change_2020 is not None else "",
					format_pct(pct_2020) if pct_2020 is not None else "",
				])


def generate_big6(data, years, out_path: Path):
	out_path.parent.mkdir(parents=True, exist_ok=True)
	header = [
		"year",
		"totalPassengers",
		"changeYoY",
		"%changeYoy",
		"changeSince2015",
		"%changeSince2015",
		"changeSince2019",
		"%changeSince2019",
		"changeSince2020",
		"%changeSince2020",
	]

	# compute totals per year
	totals = {}
	for y in years:
		s = 0
		any_data = False
		for info in data.values():
			p = info["passengers"].get(y)
			if p is not None:
				s += p
				any_data = True
		totals[y] = s if any_data else None

	with out_path.open("w", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)
		writer.writerow(header)

		base2015 = totals.get(years[0])
		for y in years:
			total = totals.get(y)
			prev = totals.get(y - 1)

			change_yoy = None
			pct_yoy = None
			if total is not None and prev is not None:
				change_yoy = total - prev
				pct_yoy = safe_div(change_yoy, prev)

			change_2015 = None
			pct_2015 = None
			if total is not None and base2015 is not None:
				change_2015 = total - base2015
				pct_2015 = safe_div(change_2015, base2015)

			# since 2019 and 2020 for totals
			base2019 = totals.get(2019)
			change_2019 = None
			pct_2019 = None
			if total is not None and base2019 is not None:
				change_2019 = total - base2019
				pct_2019 = safe_div(change_2019, base2019)

			base2020 = totals.get(2020)
			change_2020 = None
			pct_2020 = None
			if total is not None and base2020 is not None:
				change_2020 = total - base2020
				pct_2020 = safe_div(change_2020, base2020)

			writer.writerow([
				y,
				total if total is not None else "",
				change_yoy if change_yoy is not None else "",
				format_pct(pct_yoy) if pct_yoy is not None else "",
				change_2015 if change_2015 is not None else "",
				format_pct(pct_2015) if pct_2015 is not None else "",
				change_2019 if change_2019 is not None else "",
				format_pct(pct_2019) if pct_2019 is not None else "",
				change_2020 if change_2020 is not None else "",
				format_pct(pct_2020) if pct_2020 is not None else "",
			])


def main():
	repo_root = Path(__file__).resolve().parent
	input_csv = repo_root / "airfare-data" / "montana-enplanements-2015-2024.csv"
	if not input_csv.exists():
		print(f"Input file not found: {input_csv}")
		sys.exit(1)

	rows = read_enplanements(input_csv)
	if not rows:
		print("No rows in input file")
		sys.exit(1)

	years = parse_year_columns(rows[0].keys())
	data = build_airport_data(rows, years)

	out_dir = repo_root / "enplanement-analysis"
	by_airport = out_dir / "by-airport.csv"
	big6 = out_dir / "big-6.csv"

	generate_by_airport(data, years, by_airport)
	generate_big6(data, years, big6)

	print(f"Wrote: {by_airport}")
	print(f"Wrote: {big6}")


if __name__ == "__main__":
	main()
