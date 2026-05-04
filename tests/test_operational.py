import os

import pytest
from fastapi.testclient import TestClient

os.environ["SERVER_MODE"] = "1"

from server.app.main import app


class TestOperationalAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_compute_operational_endpoint(self, client):
        request_data = {
            "bottom_level": 0.1,
            "downstream_water_level": 1.8,
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.1,
            "labyrinth_length": 7.7,
            "labyrinth_key_angle": 7.0,
            "D": 0.5,
            "discharge_vector": [2.09, 2.79, 6.01, 11.9, 13.9, 16.3, 16.5, 18.6, 20.5, 22.9, 24.5],
            "downstream_water_level_vector": [1.07, 1.15, 1.19, 1.25, 1.38, 1.39, 1.74, 1.74, 1.94, 2.67, 2.67],
            "interpolation_method": "exponential",
            "flap_gate_bottom_level": 0.1,
            "flap_gate_downstream_water_level": 1.09,
            "flap_gate_discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": 74.0,
            "design_upstream_water_level": 2.2,
            "max_flap_gate_angle": 90.0,
            "fish_body_height": 0.4,
        }

        response = client.post("/operational", json=request_data)
        assert response.status_code == 200

        data = response.json()
        # Check that response contains expected fields
        assert "results" in data
        assert "results_events" in data
        assert "warnings" in data

        # Check that results contain expected fields
        assert len(data["results"]) > 0
        assert len(data["results_events"]) > 0

        # Check structure of a result point
        first_result = data["results"][0]
        expected_fields = [
            "discharge",
            "downstream_water_level",
            "upstream_water_level",
            "labyrinth_discharge",
            "flap_gate_discharge",
            "flap_gate_angle",
            "labyrinth_head_over_crest",
            "flap_gate_head_over_crest",
        ]

        for field in expected_fields:
            assert field in first_result

        assert first_result["labyrinth_head_over_crest"] is not None

        # Basic sanity checks
        assert first_result["discharge"] > 0
        assert first_result["labyrinth_discharge"] >= 0
        assert first_result["flap_gate_discharge"] >= 0

    def test_compute_operational_endpoint_with_warnings(self, client):
        request_data = {
            "bottom_level": -10.0,  # Invalid: negative (generates warning)
            "downstream_water_level": 1.8,
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.1,
            "labyrinth_length": 7.7,
            "labyrinth_key_angle": 7.0,
            "D": 0.5,
            "discharge_vector": [2.09, 2.79, 6.01],
            "downstream_water_level_vector": [1.07, 1.15, 1.19],
            "interpolation_method": "exponential",
            "flap_gate_bottom_level": 0.1,
            "flap_gate_downstream_water_level": 1.09,
            "flap_gate_discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": 74.0,
            "design_upstream_water_level": 2.2,
            "max_flap_gate_angle": 90.0,
            "fish_body_height": 0.4,
        }

        response = client.post("/operational", json=request_data)
        assert response.status_code == 200  # Should succeed but with warnings

        data = response.json()
        assert "warnings" in data
        assert data["warnings"] is not None
        assert len(data["warnings"]) > 0
        assert any("SohleHoehe Wert ist negative" in warning for warning in data["warnings"])

    def test_compute_operational_endpoint_invalid_input(self, client):
        request_data = {
            "bottom_level": 2.0,
            "downstream_water_level": 1.0,  # Invalid: below bottom level (UW - Sh <= 0)
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.1,
            "labyrinth_length": 7.7,
            "labyrinth_key_angle": 7.0,
            "D": 0.5,
            "discharge_vector": [2.09, 2.79, 6.01],
            "downstream_water_level_vector": [1.07, 1.15, 1.19],
            "interpolation_method": "exponential",
            "flap_gate_bottom_level": 0.1,
            "flap_gate_downstream_water_level": 1.09,
            "flap_gate_discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": 74.0,
            "design_upstream_water_level": 2.2,
            "max_flap_gate_angle": 90.0,
            "fish_body_height": 0.4,
        }

        response = client.post("/operational", json=request_data)
        assert response.status_code == 422  # Unprocessable Entity

        data = response.json()
        assert "detail" in data
        assert "message" in data["detail"]
        assert "errors" in data["detail"]

    def test_compute_operational_endpoint_missing_required_param(self, client):
        # Test that missing required parameters return 422 with validation error
        request_data = {
            # "bottom_level" is missing
            "downstream_water_level": 1.8,
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.1,
            "labyrinth_length": 7.7,
            "labyrinth_key_angle": 7.0,
            "D": 0.5,
            "discharge_vector": [2.09, 2.79, 6.01],
            "downstream_water_level_vector": [1.07, 1.15, 1.19],
            "interpolation_method": "exponential",
            "flap_gate_bottom_level": 0.1,
            "flap_gate_downstream_water_level": 1.09,
            "flap_gate_discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": 74.0,
            "design_upstream_water_level": 2.2,
            "max_flap_gate_angle": 90.0,
            "fish_body_height": 0.4,
        }

        response = client.post("/operational", json=request_data)
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert any("bottom_level" in str(error) and "missing" in str(error).lower() for error in data["detail"])

    def test_compute_operational_endpoint_flap_angle_range(self, client):
        request_data = {
            "bottom_level": 0.1,
            "downstream_water_level": 1.8,
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.1,
            "labyrinth_length": 7.7,
            "labyrinth_key_angle": 7.0,
            "D": 0.5,
            "discharge_vector": [2.09, 2.79, 6.01],
            "downstream_water_level_vector": [1.07, 1.15, 1.19],
            "interpolation_method": "exponential",
            "flap_gate_bottom_level": 0.1,
            "flap_gate_downstream_water_level": 1.09,
            "flap_gate_discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": -5.0,
            "design_upstream_water_level": 2.2,
            "max_flap_gate_angle": 90.0,
            "fish_body_height": 0.4,
        }

        response = client.post("/operational", json=request_data)
        assert response.status_code == 422

        data = response.json()
        errors = data["detail"]["errors"]
        assert any("Klappenwinkel β" in error.get("msg", "") for error in errors)

    def test_compute_operational_endpoint_max_flap_angle_range(self, client):
        request_data = {
            "bottom_level": 0.1,
            "downstream_water_level": 1.8,
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.1,
            "labyrinth_length": 7.7,
            "labyrinth_key_angle": 7.0,
            "D": 0.5,
            "discharge_vector": [2.09, 2.79, 6.01],
            "downstream_water_level_vector": [1.07, 1.15, 1.19],
            "interpolation_method": "exponential",
            "flap_gate_bottom_level": 0.1,
            "flap_gate_downstream_water_level": 1.09,
            "flap_gate_discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": 74.0,
            "design_upstream_water_level": 2.2,
            "max_flap_gate_angle": 120.0,
            "fish_body_height": 0.4,
        }

        response = client.post("/operational", json=request_data)
        assert response.status_code == 422

        data = response.json()
        errors = data["detail"]["errors"]
        assert any("Maximaler Klappenwinkel" in error.get("msg", "") for error in errors)

    def test_compute_operational_endpoint_empty_vectors(self, client):
        request_data = {
            "bottom_level": 0.1,
            "downstream_water_level": 1.8,
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.1,
            "labyrinth_length": 7.7,
            "labyrinth_key_angle": 7.0,
            "D": 0.5,
            "discharge_vector": [],  # Empty vector
            "downstream_water_level_vector": [1.07, 1.15, 1.19],
            "interpolation_method": "exponential",
            "flap_gate_bottom_level": 0.1,
            "flap_gate_downstream_water_level": 1.09,
            "flap_gate_discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": 74.0,
            "design_upstream_water_level": 2.2,
            "max_flap_gate_angle": 90.0,
            "fish_body_height": 0.4,
        }

        response = client.post("/operational", json=request_data)
        assert response.status_code == 422  # Unprocessable Entity

        data = response.json()
        assert "detail" in data
        assert "message" in data["detail"]
        assert "errors" in data["detail"]
        assert any("discharge_vector" in str(error).lower() or "empty" in str(error).lower() for error in data["detail"]["errors"])

    def test_compute_operational_endpoint_different_vector_lengths(self, client):
        request_data = {
            "bottom_level": 0.1,
            "downstream_water_level": 1.8,
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.1,
            "labyrinth_length": 7.7,
            "labyrinth_key_angle": 7.0,
            "D": 0.5,
            "discharge_vector": [2.09, 2.79, 6.01, 11.9, 13.9],  # 5 elements
            "downstream_water_level_vector": [1.07, 1.15, 1.19],  # 3 elements
            "interpolation_method": "exponential",
            "flap_gate_bottom_level": 0.1,
            "flap_gate_downstream_water_level": 1.09,
            "flap_gate_discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": 74.0,
            "design_upstream_water_level": 2.2,
            "max_flap_gate_angle": 90.0,
            "fish_body_height": 0.4,
        }

        response = client.post("/operational", json=request_data)
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert "message" in data["detail"]
        assert "errors" in data["detail"]
        assert any("same length" in str(error).lower() or "length" in str(error).lower() for error in data["detail"]["errors"])

    def test_compute_operational_endpoint_different_interpolation_methods(self, client):
        """Test different interpolation methods"""
        base_request = {
            "bottom_level": 0.1,
            "downstream_water_level": 1.8,
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.1,
            "labyrinth_length": 7.7,
            "labyrinth_key_angle": 7.0,
            "D": 0.5,
            "discharge_vector": [2.09, 2.79, 6.01, 11.9, 13.9],
            "downstream_water_level_vector": [1.07, 1.15, 1.19, 1.25, 1.38],
            "flap_gate_bottom_level": 0.1,
            "flap_gate_downstream_water_level": 1.09,
            "flap_gate_discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": 74.0,
            "design_upstream_water_level": 2.2,
            "max_flap_gate_angle": 90.0,
            "fish_body_height": 0.4,
        }

        # Test exponential interpolation (default)
        request_data = {**base_request, "interpolation_method": "exponential"}
        response = client.post("/operational", json=request_data)
        assert response.status_code == 200
        assert len(response.json()["results"]) > 0

        # Test linear interpolation
        request_data = {**base_request, "interpolation_method": "linear"}
        response = client.post("/operational", json=request_data)
        assert response.status_code == 200
        assert len(response.json()["results"]) > 0
