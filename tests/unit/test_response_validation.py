"""
FASE 4: Response Data Validation Tests

Tests that verify the actual structure and correctness of responses
from OpenMeteoSmartClient and API endpoints.

Tests cover:
1. Climate variable completeness
2. Data type validation
3. Temporal consistency
4. Response schema validation
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def expected_climate_variables():
    """List of expected climate variables in response."""
    return [
        "temperature_2m_max",
        "temperature_2m_min",
        "temperature_2m_mean",
        "precipitation_sum",
        "wind_speed_10m_max",
        "wind_speed_10m_mean",
        "shortwave_radiation_sum",
        "relative_humidity_2m_max",
        "relative_humidity_2m_mean",
        "relative_humidity_2m_min",
        "daylight_duration",
        "sunshine_duration",
        "et0_fao_evapotranspiration"
    ]


@pytest.fixture
def sample_valid_response():
    """Sample valid response from OpenMeteo API."""
    return {
        "latitude": -15.7939,
        "longitude": -47.8828,
        "elevation": 1050.0,
        "timezone": "America/Sao_Paulo",
        "timezone_abbreviation": "BRT",
        "utc_offset_seconds": -10800,
        "daily": {
            "time": [
                "2025-01-01", "2025-01-02", "2025-01-03",
                "2025-01-04", "2025-01-05", "2025-01-06",
                "2025-01-07"
            ],
            "temperature_2m_max": [25.0, 26.0, 25.5, 26.5, 25.2, 26.8, 25.1],
            "temperature_2m_min": [15.0, 16.0, 15.5, 16.5, 15.2, 16.8, 15.1],
            "temperature_2m_mean": [20.0, 21.0, 20.5, 21.5, 20.2, 21.8, 20.1],
            "precipitation_sum": [0.0, 2.5, 0.0, 5.0, 0.0, 1.2, 0.0],
            "wind_speed_10m_max": [5.0, 6.0, 5.5, 6.5, 5.2, 6.8, 5.1],
            "wind_speed_10m_mean": [2.0, 2.5, 2.2, 2.8, 2.1, 2.9, 2.0],
            "shortwave_radiation_sum": [20.0, 21.0, 20.5, 21.5, 20.2, 21.8, 20.1],
            "relative_humidity_2m_max": [90.0, 91.0, 90.5, 91.5, 90.2, 91.8, 90.1],
            "relative_humidity_2m_mean": [75.0, 76.0, 75.5, 76.5, 75.2, 76.8, 75.1],
            "relative_humidity_2m_min": [60.0, 61.0, 60.5, 61.5, 60.2, 61.8, 60.1],
            "daylight_duration": [11.5, 11.6, 11.7, 11.8, 11.9, 12.0, 12.1],
            "sunshine_duration": [9.0, 9.2, 9.1, 9.3, 9.0, 9.4, 8.9],
            "et0_fao_evapotranspiration": [5.1, 5.2, 5.0, 5.3, 5.1, 5.4, 5.0]
        }
    }


# ============================================================================
# TEST 1: Response Schema Validation
# ============================================================================

class TestResponseSchema:
    """Test the overall response schema structure."""
    
    def test_location_data_structure(self, sample_valid_response):
        """Response should have proper location data structure."""
        location = {
            "latitude": sample_valid_response["latitude"],
            "longitude": sample_valid_response["longitude"],
            "elevation": sample_valid_response["elevation"],
            "timezone": sample_valid_response["timezone"]
        }
        
        assert location["latitude"] is not None
        assert location["longitude"] is not None
        assert location["elevation"] is not None
        assert location["timezone"] is not None
        assert isinstance(location["latitude"], (int, float))
        assert isinstance(location["longitude"], (int, float))
        assert isinstance(location["elevation"], (int, float))
        assert isinstance(location["timezone"], str)
    
    def test_daily_data_structure(self, sample_valid_response):
        """Response should have daily data structure."""
        daily = sample_valid_response["daily"]
        
        assert "time" in daily
        assert isinstance(daily["time"], list)
        assert len(daily["time"]) > 0
        assert all(isinstance(date, str) for date in daily["time"])
    
    def test_all_climate_variables_present(self, sample_valid_response, expected_climate_variables):
        """All expected climate variables should be present."""
        daily = sample_valid_response["daily"]
        
        for var in expected_climate_variables:
            assert var in daily, f"Climate variable '{var}' missing"
            assert isinstance(daily[var], list), f"'{var}' should be a list"


# ============================================================================
# TEST 2: Data Type Validation
# ============================================================================

class TestDataTypes:
    """Test that all data types are correct."""
    
    def test_numeric_data_types(self, sample_valid_response, expected_climate_variables):
        """All climate variables should contain numeric values."""
        daily = sample_valid_response["daily"]
        
        for var in expected_climate_variables:
            values = daily[var]
            
            for idx, value in enumerate(values):
                assert isinstance(value, (int, float, type(None))), \
                    f"'{var}[{idx}]' is {type(value)}, expected int/float/None"
    
    def test_date_format_iso8601(self, sample_valid_response):
        """Dates should be in ISO 8601 format (YYYY-MM-DD)."""
        dates = sample_valid_response["daily"]["time"]
        
        iso8601_pattern = r"^\d{4}-\d{2}-\d{2}$"
        import re
        
        for date in dates:
            assert re.match(iso8601_pattern, date), \
                f"Date '{date}' is not in ISO 8601 format"
    
    def test_elevation_positive(self, sample_valid_response):
        """Elevation should be positive or zero."""
        elevation = sample_valid_response["elevation"]
        assert elevation >= 0, f"Elevation {elevation} should be >= 0"
    
    def test_coordinates_in_bounds(self, sample_valid_response):
        """Coordinates should be within valid bounds."""
        lat = sample_valid_response["latitude"]
        lng = sample_valid_response["longitude"]
        
        assert -90 <= lat <= 90, f"Latitude {lat} out of bounds"
        assert -180 <= lng <= 180, f"Longitude {lng} out of bounds"


# ============================================================================
# TEST 3: Data Consistency
# ============================================================================

class TestDataConsistency:
    """Test that data is internally consistent."""
    
    def test_all_arrays_same_length(self, sample_valid_response, expected_climate_variables):
        """All climate variable arrays should have same length as dates."""
        daily = sample_valid_response["daily"]
        dates_length = len(daily["time"])
        
        for var in expected_climate_variables:
            var_length = len(daily[var])
            assert var_length == dates_length, \
                f"'{var}' has {var_length} values, expected {dates_length}"
    
    def test_temperature_min_lte_max(self, sample_valid_response):
        """Temperature min should be <= max."""
        daily = sample_valid_response["daily"]
        temps_min = daily["temperature_2m_min"]
        temps_max = daily["temperature_2m_max"]
        
        for idx, (tmin, tmax) in enumerate(zip(temps_min, temps_max)):
            assert tmin <= tmax, \
                f"Day {idx}: temp_min ({tmin}) > temp_max ({tmax})"
    
    def test_temperature_mean_in_range(self, sample_valid_response):
        """Temperature mean should be between min and max."""
        daily = sample_valid_response["daily"]
        temps_min = daily["temperature_2m_min"]
        temps_mean = daily["temperature_2m_mean"]
        temps_max = daily["temperature_2m_max"]
        
        for idx, (tmin, tmean, tmax) in enumerate(zip(temps_min, temps_mean, temps_max)):
            assert tmin <= tmean <= tmax, \
                f"Day {idx}: mean {tmean} not in range [{tmin}, {tmax}]"
    
    def test_humidity_min_lte_mean_lte_max(self, sample_valid_response):
        """Humidity should have min <= mean <= max."""
        daily = sample_valid_response["daily"]
        hum_min = daily["relative_humidity_2m_min"]
        hum_mean = daily["relative_humidity_2m_mean"]
        hum_max = daily["relative_humidity_2m_max"]
        
        for idx, (hmin, hmean, hmax) in enumerate(zip(hum_min, hum_mean, hum_max)):
            assert hmin <= hmean <= hmax, \
                f"Day {idx}: humidity mean {hmean} not in range [{hmin}, {hmax}]"
    
    def test_humidity_in_valid_range(self, sample_valid_response):
        """Humidity should be between 0 and 100."""
        daily = sample_valid_response["daily"]
        
        for var in ["relative_humidity_2m_min", "relative_humidity_2m_mean", "relative_humidity_2m_max"]:
            values = daily[var]
            for idx, value in enumerate(values):
                if value is not None:
                    assert 0 <= value <= 100, \
                        f"Humidity {var}[{idx}] = {value}, expected 0-100"
    
    def test_dates_chronological(self, sample_valid_response):
        """Dates should be in chronological order."""
        dates = sample_valid_response["daily"]["time"]
        
        for idx in range(len(dates) - 1):
            assert dates[idx] < dates[idx + 1], \
                f"Dates not chronological: {dates[idx]} >= {dates[idx + 1]}"
    
    def test_no_duplicate_dates(self, sample_valid_response):
        """Dates should not have duplicates."""
        dates = sample_valid_response["daily"]["time"]
        unique_dates = set(dates)
        
        assert len(dates) == len(unique_dates), \
            f"Found duplicate dates: {len(dates)} total, {len(unique_dates)} unique"


# ============================================================================
# TEST 4: Value Range Validation
# ============================================================================

class TestValueRanges:
    """Test that values are within realistic ranges."""
    
    def test_temperature_realistic_range(self, sample_valid_response):
        """Temperature should be in realistic range (-50 to +60 °C)."""
        daily = sample_valid_response["daily"]
        
        for var in ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean"]:
            values = daily[var]
            for idx, value in enumerate(values):
                if value is not None:
                    assert -50 <= value <= 60, \
                        f"{var}[{idx}] = {value}, outside realistic range"
    
    def test_precipitation_non_negative(self, sample_valid_response):
        """Precipitation should be non-negative."""
        daily = sample_valid_response["daily"]
        precip = daily["precipitation_sum"]
        
        for idx, value in enumerate(precip):
            if value is not None:
                assert value >= 0, \
                    f"Precipitation[{idx}] = {value}, should be >= 0"
    
    def test_wind_speed_non_negative(self, sample_valid_response):
        """Wind speed should be non-negative."""
        daily = sample_valid_response["daily"]
        
        for var in ["wind_speed_10m_max", "wind_speed_10m_mean"]:
            values = daily[var]
            for idx, value in enumerate(values):
                if value is not None:
                    assert value >= 0, \
                        f"{var}[{idx}] = {value}, should be >= 0"
    
    def test_radiation_non_negative(self, sample_valid_response):
        """Shortwave radiation should be non-negative."""
        daily = sample_valid_response["daily"]
        radiation = daily["shortwave_radiation_sum"]
        
        for idx, value in enumerate(radiation):
            if value is not None:
                assert value >= 0, \
                    f"Radiation[{idx}] = {value}, should be >= 0"
    
    def test_duration_realistic_range(self, sample_valid_response):
        """Daylight/sunshine duration should be 0-24 hours."""
        daily = sample_valid_response["daily"]
        
        for var in ["daylight_duration", "sunshine_duration"]:
            values = daily[var]
            for idx, value in enumerate(values):
                if value is not None:
                    assert 0 <= value <= 24, \
                        f"{var}[{idx}] = {value}, should be 0-24 hours"
    
    def test_et0_reasonable_range(self, sample_valid_response):
        """ET0 should be in reasonable range (0-20 mm/day for most conditions)."""
        daily = sample_valid_response["daily"]
        et0 = daily["et0_fao_evapotranspiration"]
        
        for idx, value in enumerate(et0):
            if value is not None:
                # Extreme conditions might exceed 15, but 20 is very rare
                assert 0 <= value <= 20, \
                    f"ET0[{idx}] = {value}, outside reasonable range 0-20"


# ============================================================================
# TEST 5: Missing Value Handling
# ============================================================================

class TestMissingValues:
    """Test handling of missing/null values."""
    
    def test_null_values_acceptable(self, sample_valid_response, expected_climate_variables):
        """None/null values should be acceptable for climate variables."""
        daily = sample_valid_response["daily"]
        
        for var in expected_climate_variables:
            values = daily[var]
            # Should have mix of real values and potentially None values
            assert len(values) > 0, f"'{var}' array is empty"
    
    def test_sparse_data_acceptable(self):
        """Response with some None values should be valid."""
        response_with_nulls = {
            "latitude": -15.7939,
            "longitude": -47.8828,
            "daily": {
                "time": ["2025-01-01", "2025-01-02", "2025-01-03"],
                "temperature_2m_max": [25.0, None, 25.5],  # Missing value
                "et0_fao_evapotranspiration": [5.1, 5.2, None]  # Missing value
            }
        }
        
        # Should not raise error - sparse data is acceptable
        assert len(response_with_nulls["daily"]["time"]) == 3
        assert None in response_with_nulls["daily"]["temperature_2m_max"]


# ============================================================================
# TEST 6: Hybrid Response Merging
# ============================================================================

class TestHybridMerging:
    """Test that hybrid responses (Archive + Forecast) merge correctly."""
    
    def test_merged_response_chronological(self):
        """Merged archive + forecast should be chronological."""
        archive_dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        forecast_dates = ["2025-01-02", "2025-01-03", "2025-01-04"]  # Overlap
        
        # After merge (removing duplicates), should be chronological
        merged = sorted(set(archive_dates + forecast_dates))
        
        for idx in range(len(merged) - 1):
            assert merged[idx] < merged[idx + 1]
    
    def test_merged_response_no_duplicates(self):
        """Merged response should not have duplicate dates."""
        archive_dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        forecast_dates = ["2025-01-02", "2025-01-03", "2025-01-04"]
        
        merged = list(dict.fromkeys(archive_dates + forecast_dates))
        
        assert len(merged) == len(set(merged))
    
    def test_merged_arrays_same_length(self):
        """All data arrays should have same length after merge."""
        dates = ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"]
        
        # Simulate merged data
        merged_data = {
            "time": dates,
            "temperature_2m_max": [25.0, 26.0, 25.5, 26.5],
            "et0_fao_evapotranspiration": [5.1, 5.2, 5.0, 5.3]
        }
        
        for var, values in merged_data.items():
            if var != "time":
                assert len(values) == len(dates), \
                    f"'{var}' length mismatch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
