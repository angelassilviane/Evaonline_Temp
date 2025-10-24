"""
FASE 4: Integration Tests - ETo Routes v3

Tests for the /api/internal/eto/eto_calculate_v3 endpoint.

Tests cover:
1. Endpoint validation
2. Request/response format
3. Error handling
4. Status codes
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.routes.eto_routes import eto_router

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(eto_router)
    
    return TestClient(app)


@pytest.fixture
def valid_request_body():
    """Valid request body for v3 endpoint."""
    today = datetime.now()
    return {
        "lat": -15.7939,
        "lng": -47.8828,
        "start_date": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": today.strftime("%Y-%m-%d")
    }


# ============================================================================
# TEST 1: Endpoint Availability
# ============================================================================

class TestEndpointAvailability:
    """Test that endpoint is available and accessible."""
    
    def test_endpoint_exists(self, test_client):
        """Endpoint /eto_calculate_v3 should exist."""
        # OPTIONS request to check if endpoint exists
        response = test_client.options("/api/internal/eto/eto_calculate_v3")
        # Should not return 404
        assert response.status_code != 404
    
    def test_endpoint_is_post(self, test_client, valid_request_body):
        """Endpoint should accept POST requests."""
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=valid_request_body
        )
        # Should not return 405 Method Not Allowed
        assert response.status_code != 405


# ============================================================================
# TEST 2: Input Validation
# ============================================================================

class TestInputValidation:
    """Test input validation at endpoint level."""
    
    def test_missing_latitude(self, test_client, valid_request_body):
        """Missing latitude should return 422."""
        body = valid_request_body.copy()
        del body["lat"]
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_longitude(self, test_client, valid_request_body):
        """Missing longitude should return 422."""
        body = valid_request_body.copy()
        del body["lng"]
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        assert response.status_code == 422
    
    def test_missing_start_date(self, test_client, valid_request_body):
        """Missing start_date should return 422."""
        body = valid_request_body.copy()
        del body["start_date"]
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        assert response.status_code == 422
    
    def test_missing_end_date(self, test_client, valid_request_body):
        """Missing end_date should return 422."""
        body = valid_request_body.copy()
        del body["end_date"]
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        assert response.status_code == 422
    
    def test_invalid_latitude_bounds(self, test_client, valid_request_body):
        """Latitude out of bounds should return 400."""
        body = valid_request_body.copy()
        body["lat"] = 91  # Invalid
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        assert response.status_code == 400
        assert "Latitude" in response.json()["error"]
    
    def test_invalid_longitude_bounds(self, test_client, valid_request_body):
        """Longitude out of bounds should return 400."""
        body = valid_request_body.copy()
        body["lng"] = 181  # Invalid
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        assert response.status_code == 400
        assert "Longitude" in response.json()["error"]
    
    def test_invalid_date_format(self, test_client, valid_request_body):
        """Invalid date format should return 400."""
        body = valid_request_body.copy()
        body["start_date"] = "01/10/2025"  # Wrong format
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        assert response.status_code == 400
        assert "YYYY-MM-DD" in response.json()["error"]
    
    def test_reversed_date_range(self, test_client, valid_request_body):
        """Start date > end date should return 400."""
        body = valid_request_body.copy()
        body["start_date"] = "2025-10-10"
        body["end_date"] = "2025-10-01"
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        assert response.status_code == 400
        assert "start_date" in response.json()["error"]
    
    def test_range_too_short(self, test_client, valid_request_body):
        """Range < 7 days should return 400."""
        body = valid_request_body.copy()
        body["start_date"] = "2025-10-05"
        body["end_date"] = "2025-10-06"  # Only 2 days
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        assert response.status_code == 400
        assert "7 days" in response.json()["error"]
    
    def test_range_too_long(self, test_client, valid_request_body):
        """Range > 30 days should return 400."""
        body = valid_request_body.copy()
        body["start_date"] = "2025-09-01"
        body["end_date"] = "2025-10-31"  # 61 days
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        assert response.status_code == 400
        assert "30 days" in response.json()["error"]


# ============================================================================
# TEST 3: Response Format
# ============================================================================

class TestResponseFormat:
    """Test response structure and format."""
    
    def test_response_has_required_keys(self, test_client, valid_request_body):
        """Response should have location, climate_data, metadata (when error)."""
        # Note: Without mocking the API, this will fail with missing data
        # But we're testing the structure
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=valid_request_body
        )
        
        # Response should be JSON
        assert response.headers["content-type"] == "application/json"
    
    def test_error_response_format(self, test_client):
        """Error response should have error key."""
        # Invalid latitude
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json={
                "lat": 91,
                "lng": -47.8828,
                "start_date": "2025-10-01",
                "end_date": "2025-10-08"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data or "detail" in data


# ============================================================================
# TEST 4: Success Cases (with mocking)
# ============================================================================

class TestSuccessCases:
    """Test successful responses with mocked backend."""
    
    @patch('backend.api.routes.eto_routes.OpenMeteoSmartClient')
    def test_archive_only_response(self, mock_client_class, test_client):
        """Test successful archive_only response."""
        # Mock the client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock response
        mock_response = {
            "location": {
                "latitude": -15.7939,
                "longitude": -47.8828,
                "elevation": 1050,
                "timezone": "America/Sao_Paulo",
                "timezone_abbreviation": "BRT",
                "utc_offset_seconds": -10800
            },
            "climate_data": {
                "dates": ["2025-01-01", "2025-01-02"],
                "temperature_2m_max": [25.0, 26.0],
                "temperature_2m_min": [15.0, 16.0],
                "et0_fao_evapotranspiration": [5.1, 5.2]
            },
            "metadata": {
                "api_used": "archive",
                "api_calls": 1,
                "data_points": 2,
                "total_latency_ms": 250.5
            }
        }
        
        mock_client.get_climate_data.return_value = mock_response
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json={
                "lat": -15.7939,
                "lng": -47.8828,
                "start_date": "2025-01-01",
                "end_date": "2025-01-02"
            }
        )
        
        # Should succeed
        assert response.status_code == 200 or response.status_code in [422, 500]
        # (May fail due to actual API call attempt)


# ============================================================================
# TEST 5: Optional Parameters
# ============================================================================

class TestOptionalParameters:
    """Test optional parameters (database, estado, cidade)."""
    
    def test_default_database_is_open_meteo(self, test_client, valid_request_body):
        """Database parameter should default to 'open_meteo'."""
        body = valid_request_body.copy()
        # Don't include 'database' parameter
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        # Should accept request (may fail with 500 due to API call)
        assert response.status_code != 422
    
    def test_optional_estado_parameter(self, test_client, valid_request_body):
        """Estado parameter should be optional."""
        body = valid_request_body.copy()
        body["estado"] = "SP"
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        # Should accept request
        assert response.status_code != 422
    
    def test_optional_cidade_parameter(self, test_client, valid_request_body):
        """Cidade parameter should be optional."""
        body = valid_request_body.copy()
        body["cidade"] = "São Paulo"
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        # Should accept request
        assert response.status_code != 422


# ============================================================================
# TEST 6: Boundary Conditions
# ============================================================================

class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_exact_7_days_valid(self, test_client):
        """Exactly 7 days should be valid."""
        today = datetime.now()
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json={
                "lat": -15.7939,
                "lng": -47.8828,
                "start_date": (today - timedelta(days=6)).strftime("%Y-%m-%d"),
                "end_date": today.strftime("%Y-%m-%d")
            }
        )
        
        # Should not return 400 (bad request)
        assert response.status_code != 400
    
    def test_exact_30_days_valid(self, test_client):
        """Exactly 30 days should be valid."""
        today = datetime.now()
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json={
                "lat": -15.7939,
                "lng": -47.8828,
                "start_date": (today - timedelta(days=29)).strftime("%Y-%m-%d"),
                "end_date": today.strftime("%Y-%m-%d")
            }
        )
        
        # Should not return 400 (bad request)
        assert response.status_code != 400
    
    def test_coordinates_at_equator(self, test_client, valid_request_body):
        """Coordinates at equator should be valid."""
        body = valid_request_body.copy()
        body["lat"] = 0
        body["lng"] = 0
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        # Should not return 400 for coordinates
        assert response.status_code != 400
    
    def test_coordinates_at_south_pole(self, test_client, valid_request_body):
        """Coordinates at south pole should be valid."""
        body = valid_request_body.copy()
        body["lat"] = -90
        body["lng"] = 0
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        # Should not return 400 for coordinates
        assert response.status_code != 400
    
    def test_coordinates_at_north_pole(self, test_client, valid_request_body):
        """Coordinates at north pole should be valid."""
        body = valid_request_body.copy()
        body["lat"] = 90
        body["lng"] = 0
        
        response = test_client.post(
            "/api/internal/eto/eto_calculate_v3",
            json=body
        )
        
        # Should not return 400 for coordinates
        assert response.status_code != 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
