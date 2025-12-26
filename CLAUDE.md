# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run main data update (fetches TWSE/TPEX data, processes holdings, exports JSON)
python update_all.py

# Run broker tracking update (separate workflow)
python update_broker.py

# Build latest stock snapshot 
python build_stock_three_inst_latest.py

# Serve the frontend locally for development
python -m http.server 8000
# Then open http://localhost:8000/docs/
```

### Dependencies
- Python 3.11+ (as configured in GitHub Actions)
- requests, pandas, python-dateutil, playwright, beautifulsoup4
- No traditional package.json - this is a Python project with HTML/JS frontend

### Testing
- No formal test suite configured
- Manual testing by running scripts and verifying JSON outputs in `docs/data/`
- Frontend can be tested by serving locally and checking the web interface

## Architecture Overview

### Core Data Pipeline
This is a **Taiwan Stock Market Institutional Holdings Tracker** that:

1. **Data Fetching (`update_all.py`)**:
   - Fetches daily trading data from TWSE (上市) and TPEX (上櫃) APIs
   - TWSE T86: Three institutional investor flows
   - TWSE MI_QFIIS: Foreign holdings data  
   - TPEX flows: Three institutional flows for OTC stocks
   - TPEX QFII: Foreign holdings for OTC stocks

2. **Holdings Estimation Model**:
   - Uses **baseline correction** system via `data/inst_baseline.csv` for accurate trust/dealer holdings
   - Foreign holdings: Direct from official data (`foreign_ratio`)
   - Trust/Dealer holdings: Estimated via cumulative flows with baseline anchoring
   - Calculates combined three-institution holdings percentages

3. **Multi-Window Analysis**:
   - Tracks holdings changes across multiple time windows: `[5, 20, 60, 120]` days
   - Generates ranking files for each window showing biggest gainers/losers

4. **Data Export Structure**:
   - `docs/data/timeseries/{code}.json`: Individual stock time series
   - `docs/data/top_three_inst_change_{window}_{up|down}.json`: Rankings by change
   - `docs/data/stock_three_inst_latest.json`: Latest snapshot of all stocks

### Frontend (`docs/`)
- **Static web interface** with vanilla HTML/CSS/JS (no build process)
- Uses Chart.js for visualizations
- Features:
  - Individual stock lookup with time series charts
  - Rankings tables with filtering (market, time window)
  - Responsive design with dark mode
  - Log scale toggle for charts

### Automation (`.github/workflows/update.yml`)
- **Daily execution** at 00:10 UTC (08:10 Taipei time)
- Runs both `update_all.py` and `update_broker.py`
- Auto-commits and pushes data updates to main branch
- Uses Playwright for web scraping (requires browser installation)

### Key Files
- `update_all.py`: Main data pipeline and holdings model
- `utils_columns.py`: Helper utilities for parsing TWSE/TPEX CSV column variations
- `data/inst_baseline.csv`: Baseline holdings for model calibration (optional)
- `docs/index.html + script.js + style.css`: Frontend interface

### Data Flow
```
TWSE/TPEX APIs → Raw CSV data → Normalized DataFrames → 
Holdings Model → Time Series + Rankings → JSON Export → 
Static Frontend + GitHub Pages
```

## Important Considerations

### Data Quality
- **Encoding**: TWSE APIs return Big5/CP950 encoded data, requires special handling
- **Column Name Variations**: TWSE/TPEX frequently change CSV column names; `utils_columns.py` handles this robustly
- **Weekend/Holiday Handling**: Scripts automatically skip non-trading days

### Model Accuracy
- Foreign holdings are official/accurate
- Trust and dealer holdings are **estimated** via flow accumulation + baseline correction
- Baseline calibration via `inst_baseline.csv` significantly improves accuracy
- Model assumes no external corporate actions affecting share counts

### Browser Requirements
- Playwright dependency for some data sources
- GitHub Actions installs chromium automatically
- Local development may require `playwright install chromium`