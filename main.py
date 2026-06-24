from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, abort, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")


# -----------------------------
# Formatting helpers
# -----------------------------
def money(value: Any) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def number(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "—"


app.jinja_env.filters["money"] = money
app.jinja_env.filters["number"] = number


def team_class(value: Any) -> str:
    text = str(value or "").lower().replace(".", "").replace(" ", "-")
    return "".join(ch for ch in text if ch.isalnum() or ch == "-")


app.jinja_env.filters["team_class"] = team_class


# -----------------------------
# Data loading / filtering
# -----------------------------
def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def prepare_players(players: pd.DataFrame) -> pd.DataFrame:
    players = players.copy()
    for col in ["actual_cap_hit", "predicted_market_value", "contract_surplus", "r2", "age", "games_played", "points"]:
        if col in players.columns:
            players[col] = pd.to_numeric(players[col], errors="coerce")

    if "display_name" not in players.columns:
        players["display_name"] = players["player"]
    if "contract_type" not in players.columns:
        players["contract_type"] = ""
    if "slug" not in players.columns:
        players["slug"] = (
            players["player"].astype(str) + " " + players["team"].astype(str) + " " + players["position"].astype(str)
        ).str.lower().str.replace(r"[^a-z0-9]+", "-", regex=True).str.strip("-")
    return players


def current_scope() -> str:
    """Dataset scope controlled by ?scope=all or ?scope=std."""
    scope = request.args.get("scope", "all").lower().strip()
    return "std" if scope in {"std", "standard", "no_elc", "exclude_elc"} else "all"


def apply_scope(players: pd.DataFrame, scope: str) -> pd.DataFrame:
    if scope == "std" and "contract_type" in players.columns:
        return players[players["contract_type"].astype(str).str.upper().ne("ELC")].copy()
    return players.copy()


def build_rankings(players: pd.DataFrame, key_col: str) -> pd.DataFrame:
    d = players.dropna(subset=[key_col]).copy()
    grouped = (
        d.groupby(key_col, dropna=False)
        .agg(
            contracts=("player", "count"),
            total_surplus=("contract_surplus", "sum"),
            average_surplus=("contract_surplus", "mean"),
            actual_cap_hit=("actual_cap_hit", "sum"),
            performance_value=("predicted_market_value", "sum"),
        )
        .reset_index()
    )
    grouped["surplus_per_contract"] = grouped["average_surplus"]
    grouped["positive_contracts"] = (
        d.assign(is_positive=d["contract_surplus"] > 0)
        .groupby(key_col)["is_positive"]
        .sum()
        .reindex(grouped[key_col])
        .fillna(0)
        .astype(int)
        .values
    )
    grouped["surplus_rate"] = grouped["total_surplus"] / grouped["actual_cap_hit"].replace({0: pd.NA})
    return grouped


def load_data(scope: str | None = None) -> dict[str, pd.DataFrame]:
    scope = scope or current_scope()
    all_players = prepare_players(load_csv("nhl_market_values.csv"))
    players = apply_scope(all_players, scope)

    data = {
        "all_players": all_players,
        "players": players,
        "teams": build_rankings(players, "team"),
        "gms": build_rankings(players, "signing_gm"),
        "agents": build_rankings(players, "agent"),
        "model_summary": load_csv("model_summary.csv"),
        "model_coefficients": load_csv("model_coefficients.csv"),
    }
    return data


@app.context_processor
def inject_scope_controls():
    scope = current_scope() if request else "all"
    args_all = request.args.to_dict() if request else {}
    args_all["scope"] = "all"
    args_std = request.args.to_dict() if request else {}
    args_std["scope"] = "std"
    return {
        "scope": scope,
        "scope_label": "Standard contracts only" if scope == "std" else "All contracts",
        "all_contracts_url": f"{request.path}?" + "&".join([f"{quote(k)}={quote(str(v))}" for k, v in args_all.items()]) if request else "?scope=all",
        "std_contracts_url": f"{request.path}?" + "&".join([f"{quote(k)}={quote(str(v))}" for k, v in args_std.items()]) if request else "?scope=std",
    }


# -----------------------------
# Charts
# -----------------------------
def chart_json(fig: go.Figure) -> str:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Arial", "color": "#e5e7eb"},
        margin={"l": 40, "r": 25, "t": 45, "b": 45},
        hoverlabel={"bgcolor": "#111827"},
    )
    return fig.to_json()


def top_bar(df: pd.DataFrame, x: str, y: str, title: str, limit: int = 12) -> str:
    if df.empty or y not in df.columns:
        fig = go.Figure()
        fig.update_layout(title=title)
        return chart_json(fig)
    d = df.sort_values(y, ascending=False).head(limit).copy()
    fig = px.bar(d, x=x, y=y, title=title, text=y)
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_yaxes(tickprefix="$", separatethousands=True)
    return chart_json(fig)


def surplus_scatter(players: pd.DataFrame) -> str:
    d = players.dropna(subset=["actual_cap_hit", "predicted_market_value"]).copy()
    fig = px.scatter(
        d,
        x="actual_cap_hit",
        y="predicted_market_value",
        hover_name="display_name",
        color="contract_surplus",
        size=d["contract_surplus"].abs().clip(lower=1),
        title="Performance Value vs Actual Cap Hit",
        labels={"actual_cap_hit": "Actual Cap Hit", "predicted_market_value": "Performance Value"},
    )
    if not d.empty:
        low = min(d["actual_cap_hit"].min(), d["predicted_market_value"].min())
        high = max(d["actual_cap_hit"].max(), d["predicted_market_value"].max())
        fig.add_trace(go.Scatter(
            x=[low, high],
            y=[low, high],
            mode="lines",
            name="Cap hit = performance value",
            line={"dash": "dash", "width": 1},
        ))
    fig.update_xaxes(tickprefix="$", separatethousands=True)
    fig.update_yaxes(tickprefix="$", separatethousands=True)
    return chart_json(fig)


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    data = load_data()
    players = data["players"]
    all_players = data["all_players"]
    excluded_elcs = int((all_players["contract_type"].astype(str).str.upper() == "ELC").sum())
    r2 = players["r2"].dropna().iloc[0] if "r2" in players and players["r2"].notna().any() else None
    stats = {
        "players": len(players),
        "teams": players["team"].nunique(),
        "gms": players["signing_gm"].nunique(),
        "agents": players["agent"].nunique(),
        "r2": r2,
        "total_surplus": players["contract_surplus"].sum(),
        "excluded_elcs": excluded_elcs,
    }
    charts = {
        "scatter": surplus_scatter(players),
        "team_bar": top_bar(data["teams"], "team", "total_surplus", f"Top Teams by Total Performance Surplus — {scope_label_for_title()}", 10),
    }
    return render_template("home.html", stats=stats, charts=charts)


def scope_label_for_title() -> str:
    return "Standard Contracts Only" if current_scope() == "std" else "All Contracts"


@app.route("/players")
def players():
    data = load_data()
    df = data["players"]
    q = request.args.get("q", "").strip().lower()
    team = request.args.get("team", "")
    position = request.args.get("position", "")
    contract_type = request.args.get("contract_type", "")
    if q:
        df = df[df["player"].str.lower().str.contains(q, na=False) | df["display_name"].str.lower().str.contains(q, na=False)]
    if team:
        df = df[df["team"] == team]
    if position:
        df = df[df["position"] == position]
    if contract_type:
        df = df[df["contract_type"] == contract_type]
    df = df.sort_values("contract_surplus", ascending=False)
    all_players = data["players"]
    return render_template(
        "players.html",
        players=df.to_dict("records"),
        teams=sorted(all_players["team"].dropna().unique()),
        positions=sorted(all_players["position"].dropna().unique()),
        contract_types=sorted(all_players["contract_type"].dropna().unique()),
        q=q,
        selected_team=team,
        selected_position=position,
        selected_contract_type=contract_type,
    )


@app.route("/player/<slug>")
def player_detail(slug: str):
    # Player pages should always resolve even if user is viewing standard-only mode.
    players = load_data("all")["players"]
    row = players[players["slug"] == slug]
    if row.empty:
        abort(404)
    p = row.iloc[0].to_dict()
    metric_cols = ["points_per_60", "icf_per_60", "iscf_per_60", "ihdcf_per_60", "giveaways_per_60", "takeaways_per_60", "hits_per_60", "shots_blocked_per_60"]
    metrics = [{"name": c.replace("_", " ").title(), "value": p.get(c)} for c in metric_cols if c in p]
    return render_template("player_detail.html", p=p, metrics=metrics)


def ranking_page(kind: str):
    data = load_data()
    mapping = {
        "teams": (data["teams"], "team", "Team Rankings", "team_detail"),
        "gms": (data["gms"], "signing_gm", "GM Rankings", "gm_detail"),
        "agents": (data["agents"], "agent", "Agent Rankings", "agent_detail"),
    }
    df, key_col, title, endpoint = mapping[kind]
    sort = request.args.get("sort", "total_surplus")
    if sort not in df.columns:
        sort = "total_surplus"
    df = df.sort_values(sort, ascending=False)
    chart = top_bar(df, key_col, sort, f"Top {title} by {sort.replace('_', ' ').title()} — {scope_label_for_title()}", 15)
    return render_template("rankings.html", rows=df.to_dict("records"), key_col=key_col, title=title, endpoint=endpoint, sort=sort, chart=chart)


@app.route("/teams")
def teams():
    return ranking_page("teams")


@app.route("/gms")
def gms():
    return ranking_page("gms")


@app.route("/agents")
def agents():
    return ranking_page("agents")


def drilldown(label: str, col: str, value: str, title: str):
    players = load_data()["players"]
    df = players[players[col].astype(str) == value].sort_values("contract_surplus", ascending=False)
    if df.empty:
        # If an ELC-only entity is clicked from an old page or manually entered, fall back to all contracts.
        all_df = load_data("all")["players"]
        df = all_df[all_df[col].astype(str) == value].sort_values("contract_surplus", ascending=False)
        if df.empty:
            abort(404)
    stats = {
        "contracts": len(df),
        "total_surplus": df["contract_surplus"].sum(),
        "average_surplus": df["contract_surplus"].mean(),
        "positive": int((df["contract_surplus"] > 0).sum()),
    }
    chart = top_bar(df, "display_name", "contract_surplus", f"{value}: Performance Surplus by Player", 18)
    return render_template("drilldown.html", label=label, value=value, title=title, stats=stats, players=df.to_dict("records"), chart=chart)


@app.route("/team/<team>")
def team_detail(team: str):
    return drilldown("Team", "team", team, f"{team} Roster Drilldown")


@app.route("/gm/<path:name>")
def gm_detail(name: str):
    return drilldown("Signing GM", "signing_gm", name, f"{name} Contract Drilldown")


@app.route("/agent/<path:name>")
def agent_detail(name: str):
    return drilldown("Agent", "agent", name, f"{name} Represented Players")


@app.route("/model")
def model():
    data = load_data()
    coeffs = data["model_coefficients"].copy()
    summary = data["model_summary"].copy()
    variables = [v for v in coeffs["variable"].dropna().tolist() if str(v).lower() != "intercept"]
    return render_template("model.html", coeffs=coeffs.to_dict("records"), summary=summary.to_dict("records"), variables=variables)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
