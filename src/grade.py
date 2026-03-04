"""
grade.py
Constrained grade line optimisation (V10 algorithm).
Minimises total earthworks volume subject to:
  - max longitudinal slope (%)
  - max cut/fill height (m)
"""

import numpy as np
from scipy.optimize import minimize_scalar
from typing import List, Dict, Tuple


def _apply_grade_constraints(
    z_terrain: np.ndarray,
    x_stations: np.ndarray,
    offset: float,
    max_slope_pct: float,
    max_height_m: float,
) -> np.ndarray:
    """
    Build a constrained grade line.
    1. Start from z_terrain + offset
    2. Clip to max_height_m above/below terrain
    3. Forward + backward passes to enforce max slope
    4. Final clip to enforce height limit (priority)
    """
    g = z_terrain + offset
    g = np.clip(g, z_terrain - max_height_m, z_terrain + max_height_m)

    max_slope = max_slope_pct / 100.0
    n = len(x_stations)

    # Three smoothing passes (forward + backward) to propagate slope constraint
    for _ in range(3):
        for i in range(1, n):
            d = x_stations[i] - x_stations[i - 1]
            g[i] = np.clip(g[i], g[i - 1] - max_slope * d, g[i - 1] + max_slope * d)
        for i in range(n - 2, -1, -1):
            d = x_stations[i + 1] - x_stations[i]
            g[i] = np.clip(g[i], g[i + 1] - max_slope * d, g[i + 1] + max_slope * d)

    # Height limit is always priority 1
    return np.clip(g, z_terrain - max_height_m, z_terrain + max_height_m)


def _compute_volumes(
    z_grade: np.ndarray,
    z_terrain: np.ndarray,
    x_stations: np.ndarray,
    road_width_m: float,
    cut_slope_hv: float,
    fill_slope_hv: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute incremental cut/fill areas and volumes using prismatoid method.

    Cross-section (trapezoidal):
      cut:  A = width * h_cut + cut_slope * h_cut²
      fill: A = width * h_fill + fill_slope * h_fill²
    """
    h = z_grade - z_terrain
    h_cut = np.maximum(-h, 0.0)
    h_fill = np.maximum(h, 0.0)

    a_cut = road_width_m * h_cut + cut_slope_hv * h_cut ** 2
    a_fill = road_width_m * h_fill + fill_slope_hv * h_fill ** 2

    dx = np.diff(x_stations)
    v_cut = (a_cut[:-1] + a_cut[1:]) * 0.5 * dx
    v_fill = (a_fill[:-1] + a_fill[1:]) * 0.5 * dx

    return v_cut, v_fill, h_cut, h_fill


def compute_grade(
    station_points: List[Dict],
    road_width_m: float = 6.0,
    max_slope_pct: float = 16.0,
    max_height_m: float = 10.0,
    cut_slope_hv: float = 1.0,
    fill_slope_hv: float = 1.5,
    shrink_swell: float = 1.125,
) -> List[Dict]:
    """
    Given station points (with z_terrain_m), compute the optimal grade line
    and return enriched station dicts with cut/fill geometry.

    Args:
        station_points: from stationing.build_stationing()
        road_width_m:   platform width in metres
        max_slope_pct:  maximum longitudinal slope (%)
        max_height_m:   maximum cut or fill height (m)
        cut_slope_hv:   cut side slope H:V ratio
        fill_slope_hv:  fill side slope H:V ratio
        shrink_swell:   volume correction factor (> 1 = swell)

    Returns:
        same list enriched with z_grade_m, cut_height_m, fill_height_m,
        cut_area_m2, fill_area_m2, cut_vol_m3, fill_vol_m3 (incremental),
        cut_vol_cum_m3, fill_vol_cum_m3
    """
    x = np.array([p["station_m"] for p in station_points])
    z = np.array([p["z_terrain_m"] for p in station_points])
    n = len(x)

    def total_vol(offset):
        g = _apply_grade_constraints(z, x, offset, max_slope_pct, max_height_m)
        vc, vf, _, _ = _compute_volumes(g, z, x, road_width_m, cut_slope_hv, fill_slope_hv)
        return np.sum(vc) + np.sum(vf)

    result = minimize_scalar(
        total_vol, bounds=(-max_height_m, max_height_m), method="bounded"
    )

    g_final = _apply_grade_constraints(z, x, result.x, max_slope_pct, max_height_m)
    v_cut_inc, v_fill_inc, h_cut, h_fill = _compute_volumes(
        g_final, z, x, road_width_m, cut_slope_hv, fill_slope_hv
    )

    # Areas per station
    a_cut = road_width_m * h_cut + cut_slope_hv * h_cut ** 2
    a_fill = road_width_m * h_fill + fill_slope_hv * h_fill ** 2

    # Incremental volumes: station[0] gets 0, station[i] gets v_inc[i-1]
    v_cut_col = np.zeros(n)
    v_fill_col = np.zeros(n)
    v_cut_col[1:] = v_cut_inc
    v_fill_col[1:] = v_fill_inc

    v_cut_cum = np.cumsum(v_cut_col)
    v_fill_cum = np.cumsum(v_fill_col)

    # Grade slope per station
    g_slope = np.zeros(n)
    if n > 1:
        dz = np.diff(g_final)
        dx = np.diff(x)
        g_slope[1:] = np.where(dx > 0, dz / dx * 100, 0.0)

    enriched = []
    for i, pt in enumerate(station_points):
        enriched.append(
            {
                **pt,
                "z_grade_m": round(float(g_final[i]), 2),
                "grade_slope_pct": round(float(g_slope[i]), 2),
                "cut_height_m": round(float(h_cut[i]), 2),
                "fill_height_m": round(float(h_fill[i]), 2),
                "cut_area_m2": round(float(a_cut[i]), 2),
                "fill_area_m2": round(float(a_fill[i]), 2),
                "cut_vol_m3": round(float(v_cut_col[i]), 2),
                "fill_vol_m3": round(float(v_fill_col[i]), 2),
                "cut_vol_cum_m3": round(float(v_cut_cum[i]), 2),
                "fill_vol_cum_m3": round(float(v_fill_cum[i]), 2),
            }
        )

    return enriched
