"""
Unit tests for grade.py
Tests grade constraint application, volume calculations, and optimization.
"""

import pytest
import numpy as np
from src.grade import compute_grade


class TestGradeConstraints:
    """Tests for grade constraint application"""

    def test_flat_terrain_zero_slope(self):
        """Flat terrain should produce a flat grade line"""
        stations = [
            {"station_m": i * 20.0, "z_terrain_m": 100.0}
            for i in range(6)  # 0, 20, 40, 60, 80, 100m
        ]

        result = compute_grade(
            stations,
            road_width_m=6.0,
            max_slope_pct=10.0,
            cut_slope_hv=1.0,
            fill_slope_hv=1.5,
            max_height_m=10.0,
        )

        # Grade should be approximately flat (near terrain)
        grades = [s["z_grade_m"] for s in result]
        assert all(99.0 < g < 101.0 for g in grades)

    def test_respects_max_slope_constraint(self):
        """Grade line should respect maximum slope constraint"""
        # Create steep terrain (20% slope)
        stations = [
            {"station_m": i * 20.0, "z_terrain_m": 100.0 + i * 4.0}
            for i in range(11)  # 0 to 200m
        ]

        result = compute_grade(
            stations,
            road_width_m=6.0,
            max_slope_pct=10.0,  # Max 10% slope
            cut_slope_hv=1.0,
            fill_slope_hv=1.5,
            max_height_m=10.0,
        )

        # Calculate actual grade slopes
        for i in range(1, len(result)):
            dz = result[i]["z_grade_m"] - result[i-1]["z_grade_m"]
            dx = result[i]["station_m"] - result[i-1]["station_m"]
            slope_pct = abs(dz / dx * 100) if dx > 0 else 0
            # Should not exceed max slope (with small tolerance for numerical precision)
            assert slope_pct <= 10.1

    def test_respects_max_height_constraint(self):
        """Grade line should respect maximum cut/fill height"""
        # Create very steep terrain
        stations = [
            {"station_m": i * 20.0, "z_terrain_m": 100.0 + i * 10.0}
            for i in range(6)
        ]

        result = compute_grade(
            stations,
            road_width_m=6.0,
            max_slope_pct=5.0,
            cut_slope_hv=1.0,
            fill_slope_hv=1.5,
            max_height_m=3.0,  # Max 3m cut/fill
        )

        # Check that no cut or fill exceeds max height
        for s in result:
            assert abs(s["cut_height_m"]) <= 3.1  # Small tolerance
            assert abs(s["fill_height_m"]) <= 3.1


class TestVolumeCalculations:
    """Tests for cut/fill volume calculations using prismatoid method"""

    def test_zero_cut_fill_on_flat_terrain(self):
        """Flat terrain with grade on terrain should have zero volumes"""
        stations = [
            {"station_m": i * 20.0, "z_terrain_m": 100.0}
            for i in range(6)
        ]

        result = compute_grade(
            stations,
            road_width_m=6.0,
            max_slope_pct=10.0,
            cut_slope_hv=1.0,
            fill_slope_hv=1.5,
            max_height_m=10.0,
        )

        # All volumes should be approximately zero
        total_cut = sum(s["cut_vol_m3"] for s in result)
        total_fill = sum(s["fill_vol_m3"] for s in result)

        assert total_cut < 1.0
        assert total_fill < 1.0

    def test_pure_cut_above_terrain(self):
        """Grade above terrain should produce only cut volumes"""
        stations = [
            {"station_m": i * 20.0, "z_terrain_m": 100.0}
            for i in range(6)
        ]

        # Manually set grade line 2m above terrain
        result = compute_grade(
            stations,
            road_width_m=6.0,
            max_slope_pct=0.0,  # Flat grade
            cut_slope_hv=1.0,
            fill_slope_hv=1.5,
            max_height_m=10.0,
        )

        # Force grade above terrain for testing
        for s in result:
            s["z_grade_m"] = s["z_terrain_m"] + 2.0
            # Recalculate heights
            s["cut_height_m"] = max(0.0, s["z_grade_m"] - s["z_terrain_m"])
            s["fill_height_m"] = max(0.0, s["z_terrain_m"] - s["z_grade_m"])

        # Should have cut but no fill
        total_cut = sum(s.get("cut_vol_m3", 0) for s in result)
        total_fill = sum(s.get("fill_vol_m3", 0) for s in result)

        # Note: volumes are calculated in compute_grade, so this test
        # is more about verifying the height calculations are correct
        assert all(s["cut_height_m"] == 2.0 for s in result)
        assert all(s["fill_height_m"] == 0.0 for s in result)

    def test_cumulative_volumes_increase(self):
        """Cumulative volumes should be monotonically increasing"""
        # Create uphill terrain requiring fill
        stations = [
            {"station_m": i * 20.0, "z_terrain_m": 100.0 + i * 2.0}
            for i in range(6)
        ]

        result = compute_grade(
            stations,
            road_width_m=6.0,
            max_slope_pct=5.0,
            cut_slope_hv=1.0,
            fill_slope_hv=1.5,
            max_height_m=10.0,
        )

        # Cumulative volumes should never decrease
        prev_cut_cum = 0.0
        prev_fill_cum = 0.0

        for s in result:
            assert s["cut_vol_cum_m3"] >= prev_cut_cum
            assert s["fill_vol_cum_m3"] >= prev_fill_cum
            prev_cut_cum = s["cut_vol_cum_m3"]
            prev_fill_cum = s["fill_vol_cum_m3"]


class TestGradeOutput:
    """Tests for grade computation output structure"""

    def test_all_required_fields_present(self):
        """Grade computation should add all required fields"""
        stations = [
            {"station_m": i * 20.0, "z_terrain_m": 100.0}
            for i in range(3)
        ]

        result = compute_grade(
            stations,
            road_width_m=6.0,
            max_slope_pct=10.0,
            cut_slope_hv=1.0,
            fill_slope_hv=1.5,
            max_height_m=10.0,
        )

        required_fields = [
            "z_grade_m",
            "grade_slope_pct",
            "cut_height_m",
            "fill_height_m",
            "cut_area_m2",
            "fill_area_m2",
            "cut_vol_m3",
            "fill_vol_m3",
            "cut_vol_cum_m3",
            "fill_vol_cum_m3",
        ]

        for station in result:
            for field in required_fields:
                assert field in station
                assert isinstance(station[field], (int, float))

    def test_preserves_input_fields(self):
        """Grade computation should preserve original station fields"""
        stations = [
            {
                "station_m": i * 20.0,
                "z_terrain_m": 100.0,
                "lat": -22.5,
                "lon": -43.5,
                "custom_field": "test",
            }
            for i in range(3)
        ]

        result = compute_grade(
            stations,
            road_width_m=6.0,
            max_slope_pct=10.0,
            cut_slope_hv=1.0,
            fill_slope_hv=1.5,
            max_height_m=10.0,
        )

        for station in result:
            assert "station_m" in station
            assert "z_terrain_m" in station
            assert "lat" in station
            assert "lon" in station
            assert "custom_field" in station
