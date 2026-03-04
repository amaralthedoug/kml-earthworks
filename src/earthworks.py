"""
earthworks.py
Aggregate cut/fill results into per-segment and overall summaries.
Segment = one access alignment (file_name + access_id).
"""

import pandas as pd
from typing import List, Dict


def build_dataframe(
    alignments_data: List[Dict],
    shrink_swell: float = 1.125,
) -> pd.DataFrame:
    """
    Combine all enriched station points from multiple alignments into
    a single tidy DataFrame with file_name and access_id columns.

    Args:
        alignments_data: list of {"file_name", "access_id", "stations": [...]}
        shrink_swell: factor applied to cut volume for mass balance

    Returns:
        pd.DataFrame with all per-station columns
    """
    rows = []
    for alignment in alignments_data:
        for pt in alignment["stations"]:
            rows.append(
                {
                    "file_name": alignment["file_name"],
                    "access_id": alignment["access_id"],
                    **pt,
                }
            )

    df = pd.DataFrame(rows)

    # Mass balance: positive = waste (surplus cut), negative = borrow needed
    df["mass_balance_m3"] = (
        df["cut_vol_cum_m3"] * shrink_swell - df["fill_vol_cum_m3"]
    )

    return df


def build_segment_summary(df: pd.DataFrame, shrink_swell: float = 1.125) -> pd.DataFrame:
    """
    Produce one summary row per access alignment.

    Returns DataFrame with:
        file_name, access_id, length_m,
        cut_total_m3, fill_total_m3,
        net_m3 (cut*shrink - fill),
        borrow_m3, waste_m3
    """
    records = []
    for (file_name, access_id), grp in df.groupby(["file_name", "access_id"], sort=False):
        length_m = grp["station_m"].max()
        cut_total = grp["cut_vol_m3"].sum()
        fill_total = grp["fill_vol_m3"].sum()
        net = cut_total * shrink_swell - fill_total

        records.append(
            {
                "file_name": file_name,
                "access_id": access_id,
                "length_m": round(length_m, 1),
                "cut_total_m3": round(cut_total, 0),
                "fill_total_m3": round(fill_total, 0),
                "net_m3": round(net, 0),
                "borrow_m3": round(max(-net, 0), 0),
                "waste_m3": round(max(net, 0), 0),
            }
        )

    return pd.DataFrame(records)


def overall_kpis(summary_df: pd.DataFrame) -> Dict:
    """Return dict of overall KPI values for the header cards."""
    return {
        "total_length_m": summary_df["length_m"].sum(),
        "cut_total_m3": summary_df["cut_total_m3"].sum(),
        "fill_total_m3": summary_df["fill_total_m3"].sum(),
        "borrow_m3": summary_df["borrow_m3"].sum(),
        "waste_m3": summary_df["waste_m3"].sum(),
        "net_m3": summary_df["net_m3"].sum(),
    }
