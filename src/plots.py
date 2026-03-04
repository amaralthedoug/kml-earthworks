"""
plots.py
All Plotly figures for the kml-earthworks app.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Optional

_COLORS = px.colors.qualitative.Bold
_CUT_COLOR = "#E05252"
_FILL_COLOR = "#4A90D9"
_TERRAIN_COLOR = "#8B6914"
_GRADE_COLOR = "#1A1A2E"
_MASS_COLOR = "#7B2D8B"
_ZERO_COLOR = "#AAAAAA"


def _access_color(access_id: str, all_ids: list) -> str:
    idx = all_ids.index(access_id) if access_id in all_ids else 0
    return _COLORS[idx % len(_COLORS)]


# ─── 1. PLAN VIEW MAP ─────────────────────────────────────────────────────────

def fig_plan_view(df: pd.DataFrame) -> go.Figure:
    """Scatter mapbox with all alignments in distinct colors."""
    access_ids = df["access_id"].unique().tolist()
    fig = go.Figure()

    for acc in access_ids:
        sub = df[df["access_id"] == acc]
        color = _access_color(acc, access_ids)
        fig.add_trace(
            go.Scattermapbox(
                lat=sub["lat"],
                lon=sub["lon"],
                mode="lines+markers",
                name=acc,
                line=dict(width=3, color=color),
                marker=dict(size=4, color=color),
                customdata=np.stack(
                    [
                        sub["station_m"],
                        sub["z_terrain_m"],
                        sub.get("z_grade_m", sub["z_terrain_m"]),
                        sub.get("cut_height_m", np.zeros(len(sub))),
                        sub.get("fill_height_m", np.zeros(len(sub))),
                    ],
                    axis=-1,
                ),
                hovertemplate=(
                    "<b>%{customdata[0]:.0f} m</b><br>"
                    "Terrain: %{customdata[1]:.1f} m<br>"
                    "Grade: %{customdata[2]:.1f} m<br>"
                    "Cut: %{customdata[3]:.2f} m  Fill: %{customdata[4]:.2f} m<br>"
                    "Lat: %{lat:.6f}  Lon: %{lon:.6f}<extra>%{fullData.name}</extra>"
                ),
            )
        )

    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=13,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=480,
        legend=dict(
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#CCCCCC",
            borderwidth=1,
        ),
    )
    return fig


# ─── 2. TERRAIN vs GRADE PROFILE ──────────────────────────────────────────────

def fig_profile(df: pd.DataFrame, access_id: Optional[str] = None) -> go.Figure:
    """Terrain vs grade line profile with cut/fill shading."""
    sub = df[df["access_id"] == access_id] if access_id else df

    fig = go.Figure()

    # Shading: fill area (grade > terrain)
    fig.add_trace(
        go.Scatter(
            x=sub["station_m"],
            y=sub["z_terrain_m"],
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=sub["station_m"],
            y=sub["z_grade_m"],
            fill="tonexty",
            fillcolor="rgba(74,144,217,0.25)",
            line=dict(width=0),
            name="Fill zone",
            hoverinfo="skip",
        )
    )

    # Shading: cut area (terrain > grade)
    fig.add_trace(
        go.Scatter(
            x=sub["station_m"],
            y=sub["z_grade_m"],
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=sub["station_m"],
            y=sub["z_terrain_m"],
            fill="tonexty",
            fillcolor="rgba(224,82,82,0.25)",
            line=dict(width=0),
            name="Cut zone",
            hoverinfo="skip",
        )
    )

    # Terrain line
    fig.add_trace(
        go.Scatter(
            x=sub["station_m"],
            y=sub["z_terrain_m"],
            name="Terrain",
            line=dict(color=_TERRAIN_COLOR, width=2, dash="dot"),
            hovertemplate="Station %{x:.0f} m<br>Terrain: %{y:.2f} m<extra></extra>",
        )
    )

    # Grade line
    fig.add_trace(
        go.Scatter(
            x=sub["station_m"],
            y=sub["z_grade_m"],
            name="Grade line",
            line=dict(color=_GRADE_COLOR, width=3),
            hovertemplate="Station %{x:.0f} m<br>Grade: %{y:.2f} m<br>Slope: %{customdata:.1f}%<extra></extra>",
            customdata=sub.get("grade_slope_pct", sub["slope_pct"]),
        )
    )

    # Stake ticks every 20 m
    stakes = sub[sub["stake_20m"] == True]
    fig.add_trace(
        go.Scatter(
            x=stakes["station_m"],
            y=stakes["z_terrain_m"],
            mode="markers",
            name="Stakes (20 m)",
            marker=dict(symbol="line-ns", size=8, color="#555555", line=dict(width=1)),
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        xaxis_title="Chainage (m)",
        yaxis_title="Elevation (m)",
        height=400,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    return fig


# ─── 3. CUT / FILL BARS ───────────────────────────────────────────────────────

def fig_cut_fill_bars(df: pd.DataFrame, access_id: Optional[str] = None) -> go.Figure:
    """Bar chart of incremental cut and fill per station."""
    sub = df[df["access_id"] == access_id] if access_id else df

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=sub["station_m"],
            y=sub["cut_height_m"],
            name="Cut height (m)",
            marker_color=_CUT_COLOR,
            hovertemplate="Station %{x:.0f} m<br>Cut: %{y:.2f} m<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=sub["station_m"],
            y=-sub["fill_height_m"],
            name="Fill height (m)",
            marker_color=_FILL_COLOR,
            hovertemplate="Station %{x:.0f} m<br>Fill: %{y:.2f} m<extra></extra>",
        )
    )
    fig.update_layout(
        barmode="relative",
        xaxis_title="Chainage (m)",
        yaxis_title="Height (m)  ▲ Cut  ▼ Fill",
        height=360,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


# ─── 4. MASS DIAGRAM ──────────────────────────────────────────────────────────

def fig_mass_diagram(df: pd.DataFrame, shrink_swell: float = 1.125, access_id: Optional[str] = None) -> go.Figure:
    """Cumulative cut and fill + net balance (mass haul diagram)."""
    sub = df[df["access_id"] == access_id] if access_id else df

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=sub["station_m"],
            y=sub["cut_vol_cum_m3"],
            name="Cumulative Cut (m³)",
            line=dict(color=_CUT_COLOR, width=2),
            fill="tozeroy",
            fillcolor="rgba(224,82,82,0.12)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=sub["station_m"],
            y=sub["fill_vol_cum_m3"],
            name="Cumulative Fill (m³)",
            line=dict(color=_FILL_COLOR, width=2),
            fill="tozeroy",
            fillcolor="rgba(74,144,217,0.12)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=sub["station_m"],
            y=sub["mass_balance_m3"],
            name="Mass Balance (m³)",
            line=dict(color=_MASS_COLOR, width=2, dash="dash"),
        )
    )
    fig.add_hline(y=0, line_dash="dot", line_color=_ZERO_COLOR, annotation_text="Balance zero")

    fig.update_layout(
        xaxis_title="Chainage (m)",
        yaxis_title="Volume (m³)",
        height=360,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )
    return fig


# ─── 5. 3D VIEW ───────────────────────────────────────────────────────────────

def fig_3d(df: pd.DataFrame, access_id: Optional[str] = None) -> go.Figure:
    """3D scatter of terrain and grade line along the alignment."""
    sub = df[df["access_id"] == access_id] if access_id else df
    access_ids = df["access_id"].unique().tolist()

    fig = go.Figure()

    for acc in (sub["access_id"].unique() if access_id is None else [access_id]):
        grp = sub[sub["access_id"] == acc]
        color = _access_color(acc, access_ids)

        fig.add_trace(
            go.Scatter3d(
                x=grp["lon"],
                y=grp["lat"],
                z=grp["z_terrain_m"],
                mode="lines",
                name=f"{acc} — Terrain",
                line=dict(color=_TERRAIN_COLOR, width=3),
            )
        )
        if "z_grade_m" in grp.columns:
            fig.add_trace(
                go.Scatter3d(
                    x=grp["lon"],
                    y=grp["lat"],
                    z=grp["z_grade_m"],
                    mode="lines",
                    name=f"{acc} — Grade",
                    line=dict(color=color, width=5),
                )
            )

    fig.update_layout(
        scene=dict(
            xaxis_title="Longitude",
            yaxis_title="Latitude",
            zaxis_title="Elevation (m)",
            aspectmode="auto",
        ),
        height=500,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig
