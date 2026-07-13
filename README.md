# NHL Player Valuation Platform

An interactive analytics platform for evaluating NHL player value, contract efficiency, and roster construction using regression modeling, statistical analysis, and interactive dashboards.

## Live Application

https://nhl-performance-value-explorer-production.up.railway.app/

---

## Overview

The NHL Player Valuation Platform estimates player performance value and compares it against contract cost to identify surplus-value and underperforming contracts.

Designed as a decision-support application, the platform transforms player performance data into interactive visualizations and rankings that allow users to evaluate players, teams, general managers, and player agents from multiple perspectives.

The application automatically recalculates rankings and visualizations as users switch between all contracts and standard contracts (excluding entry-level contracts), providing a flexible environment for exploring NHL contract efficiency. :contentReference[oaicite:0]{index=0}

---

## Features

- Player valuation estimates
- Contract surplus analysis
- Team salary efficiency rankings
- General Manager rankings
- Player Agent rankings
- Interactive player profiles
- Dynamic filtering and search
- Dataset toggle (All Contracts / Exclude ELCs)
- Interactive charts and dashboards

---

## Technology Stack

### Backend
- Python
- Flask
- Pandas

### Visualization
- Plotly

### Frontend
- HTML
- CSS
- JavaScript

### Deployment
- Railway

---

## Methodology

The model estimates player performance value using regression-based statistical modeling built from publicly available NHL performance data.

Model outputs are compared against each player's current cap hit to estimate contract surplus or deficit, allowing comparisons across players, teams, general managers, and player agents.

Rather than acting as a forecasting model, the application is designed as a decision-support tool that helps users explore roster construction, salary efficiency, and contract value through interactive analytics.

---

## Application Pages

### Home Dashboard
High-level KPIs, visual summaries, and interactive charts.

### Player Explorer
Search every NHL player and compare estimated performance value with contract cost.

### Team Rankings
Compare organizations by total surplus, average surplus, and contract efficiency.

### General Manager Rankings
Evaluate roster construction using aggregated contract surplus.

### Agent Rankings
Analyze contract value created by player representation across the league.

### Player Profiles
Individual player pages with contract information, performance metrics, and valuation details.

---

## Latest Updates

- Added dataset toggle:
  - All Contracts
  - Exclude Entry-Level Contracts
- Rankings now refresh dynamically using the selected dataset.
- Interactive filtering added across dashboards.
- Team, GM, Agent, and Player pages automatically update with dataset selection.
- Improved navigation and overall application performance. :contentReference[oaicite:1]{index=1}

---

## Running Locally

```bash
pip install -r requirements.txt
python main.py
```

Open:

```
http://localhost:5000
```

---

## Future Improvements

- Multi-season historical analysis
- Additional player performance metrics
- Model comparison views
- Expanded contract visualization tools
- Exportable reports
- Advanced filtering options

---

## Author

**Michael Dunk**

Analytics Developer focused on predictive modeling, decision-support systems, and public-facing analytics applications.

LinkedIn:
https://linkedin.com/in/michaeldunkanalytics

GitHub:
https://github.com/ClutchSheets
