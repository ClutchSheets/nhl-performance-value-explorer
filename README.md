# NHL Performance Value Explorer

A Flask + Pandas + Plotly analytics app for comparing NHL player cap hits to a regression-based estimate of 2025-26 performance value.

## What changed in this version

- App language now uses **Performance Value** and **Performance Surplus** instead of broader market-value language.
- Added a global dataset toggle:
  - **All contracts**
  - **Exclude ELCs**
- The toggle refreshes home KPIs, charts, player tables, team rankings, GM rankings, agent rankings, and drilldowns.
- Rankings are recalculated dynamically from the active dataset rather than using fixed CSV ranking files.
- Player pages remain accessible regardless of the active dataset scope.

## Local run

```bash
pip install -r requirements.txt
python main.py
```

Open:

```text
http://127.0.0.1:5000
```

## Railway

Start command:

```bash
gunicorn main:app
```

The included `Procfile` already contains this command.


## v2.3 updates
- Added minimalist team abbreviation badges using color accents only. No official NHL logos or protected artwork are included.
- Standardized non-model decimal formatting to three decimal places where values are displayed as decimals.
- Kept model coefficients and regression details on the Model page at higher precision.
