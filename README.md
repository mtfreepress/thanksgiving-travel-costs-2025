# Thanksgiving Travel cost Analysis 2020-2024

## Data
### Flight cost:
- Data from [Bureau of Transportation Statistics average fare](https://www.transtats.bts.gov/averagefare/)
- Excel sheets processed by hand to extract just Montana airports. Raw excel sheets are in [airfare-data-excel-sheets](airfare-data-excel-sheets)
- Cleaned data in [airfare-data](airfare-data)

# _Notes_
- `air_travel_price_trends.py` should be run first
= `air_travel_trend_analysis.py` depends on data from price_trends so run it second

### Gasoline cost:
- Takes data from [GasBuddy.com](https://gasbuddy.com)
- Data in [gas-analysis](gas-analysis)
- Processes to calculate YoY change and change since 2020. Working to get data back to 2015 (or older)


## Purpose:
- Quantify appoxmiate percentage change of travel cost changes in Montana.
- _Gasoline data is calculated as week before and week after thanksgiving_
- _Airline ticket prices use Q4 data because it is the most granular data available. Still shows strong trend lines_

## License
- MIT License to keep things simple
- See [LICENSE](LICENSE) for more details