import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

os.environ["SERVER_MODE"] = "1"

from engineer import Labyrinth, optimize_labyrinth_geometry
from server.app.main import app


class TestLabyrinthClass:
    def test_labyrinth_initialization_and_computation(self):
        labyrinth = Labyrinth(
            bottom_level=0.1,
            downstream_water_level=1.09,
            discharge=10.0,
            labyrinth_width=15.0,
            labyrinth_height=2.2,
            labyrinth_length=8.0,
            labyrinth_key_angle=8.0,
            D=0.5,
            t=0.3,
            show_errors=False,
            show_geometry=False,
            show_results=False,
        )

        # Check that input parameters are set
        assert labyrinth.Sh == 0.1
        assert labyrinth.UW == 1.09
        assert labyrinth.Q == 10.0
        assert labyrinth.W == 15.0
        assert labyrinth.B == 8.0
        assert labyrinth.P == 2.2
        assert labyrinth.alpha == 8.0

        # Check that computed values are set
        assert hasattr(labyrinth, "N")  # Number of cycles
        assert hasattr(labyrinth, "Cd")  # Discharge coefficient
        assert hasattr(labyrinth, "v")  # Velocity
        assert hasattr(labyrinth, "hd")  # Hydraulic head
        assert hasattr(labyrinth, "Hu")  # Upstream head
        assert hasattr(labyrinth, "hu")  # Upstream water depth
        assert hasattr(labyrinth, "yu")  # Upstream specific energy

        assert labyrinth.Cd > 0  # Discharge coefficient should be positive
        assert labyrinth.v > 0  # Velocity should be positive

    def test_labyrinth_with_missing_parameters(self):
        labyrinth = Labyrinth(
            bottom_level=0.1,
            discharge=10.0,
            labyrinth_width=15.0,
            labyrinth_height=2.2,
            labyrinth_length=8.0,
            labyrinth_key_angle=8.0,
            # downstream_water_level is missing
        )

        assert labyrinth.Sh == 0.1
        assert labyrinth.UW is None
        assert labyrinth.Q == 10.0


class TestLabyrinthOptimization:
    def test_optimize_labyrinth_geometry(self):
        best_labyrinth = optimize_labyrinth_geometry(
            labyrinth=Labyrinth,
            sohleHoehe=0.1,
            UW=1.8,
            Q=20.0,
            labyrinthBreite=10.0,
            labyrinthHoehe=2.2,
            labyrinthLaengeMax=8.0,
            path="",
            show_results=False,
            show_plot=False,
        )

        assert hasattr(best_labyrinth, "B")  # Optimized length
        assert hasattr(best_labyrinth, "alpha")  # Optimized angle
        assert hasattr(best_labyrinth, "N")  # Number of cycles
        assert hasattr(best_labyrinth, "Cd")  # Discharge coefficient
        assert hasattr(best_labyrinth, "v")  # Velocity

        # Basic sanity checks
        assert best_labyrinth.B > 0  # Length should be positive
        assert 6 <= best_labyrinth.alpha <= 36  # Angle should be in expected range
        assert best_labyrinth.Cd > 0  # Discharge coefficient should be positive


class TestLabyrinthAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_compute_labyrinth_endpoint(self, client):
        request_data = {
            "bottom_level": 0.1,
            "downstream_water_level": 1.09,
            "discharge": 10.0,
            "labyrinth_width": 15.0,
            "labyrinth_height": 2.2,
            "labyrinth_length": 8.0,
            "labyrinth_key_angle": 8.0,
            "D": 0.5,
            "t": 0.3,
        }

        response = client.post("/labyrinth/compute", json=request_data)
        assert response.status_code == 200

        data = response.json()
        expected_fields = ["N", "L", "w", "l", "S", "Hu", "hu", "yu", "Cd", "v", "hd", "Hd", "rs"]

        for field in expected_fields:
            assert field in data

        assert data["Cd"] > 0  # Discharge coefficient should be positive
        assert data["v"] > 0  # Velocity should be positive

    def test_compute_labyrinth_endpoint_with_warnings(self, client):
        request_data = {
            "bottom_level": -10.0,  # Invalid: negative (generates warning)
            "downstream_water_level": 1.09,
            "discharge": 10.0,
            "labyrinth_width": 15.0,
            "labyrinth_height": 2.2,
            "labyrinth_length": 8.0,
            "labyrinth_key_angle": 8.0,
        }

        response = client.post("/labyrinth/compute", json=request_data)
        assert response.status_code == 200  # Should succeed but with warnings

        data = response.json()
        assert "warnings" in data
        assert data["warnings"] is not None
        assert len(data["warnings"]) > 0
        assert any("SohleHoehe Wert ist negative" in warning for warning in data["warnings"])

    def test_compute_labyrinth_endpoint_invalid_input(self, client):
        request_data = {
            "bottom_level": 0.1,
            "downstream_water_level": 0.05,  # Invalid: below bottom level (UW - Sh <= 0)
            "discharge": 10.0,
            "labyrinth_width": 15.0,
            "labyrinth_height": 2.2,
            "labyrinth_length": 8.0,
            "labyrinth_key_angle": 8.0,
        }

        response = client.post("/labyrinth/compute", json=request_data)
        assert response.status_code == 422  # Unprocessable Entity

        data = response.json()
        assert "detail" in data
        assert "message" in data["detail"]
        assert "errors" in data["detail"]

    def test_compute_labyrinth_endpoint_missing_required_param(self, client):
        request_data = {
            # "bottom_level" is missing
            "downstream_water_level": 1.09,
            "discharge": 10.0,
            "labyrinth_width": 15.0,
            "labyrinth_height": 2.2,
            "labyrinth_length": 8.0,
            "labyrinth_key_angle": 8.0,
        }

        response = client.post("/labyrinth/compute", json=request_data)
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert any("bottom_level" in str(error) and "missing" in str(error).lower() for error in data["detail"])

    def test_optimize_labyrinth_endpoint(self, client):
        request_data = {
            "bottom_level": 0.1,
            "downstream_water_level": 1.8,
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.2,
            "labyrinth_length_max": 8.0,
        }

        response = client.post("/labyrinth/optimize", json=request_data)
        assert response.status_code == 200

        data = response.json()
        expected_fields = ["B_best", "Angle_best", "N_best", "w_best", "l_best", "S_best", "L_best", "Hu_best", "Cd_best", "v_best"]

        for field in expected_fields:
            assert field in data

        assert data["B_best"] > 0  # Length should be positive
        assert 6 <= data["Angle_best"] <= 36  # Angle should be in expected range
        assert data["Cd_best"] > 0  # Discharge coefficient should be positive
        assert "warnings" in data

    def test_optimize_labyrinth_endpoint_with_warnings(self, client):
        request_data = {
            "bottom_level": -5.0,  # Invalid: negative (generates warning)
            "downstream_water_level": 1.8,
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.2,
            "labyrinth_length_max": 8.0,
        }

        response = client.post("/labyrinth/optimize", json=request_data)
        assert response.status_code == 200  # Should succeed but with warnings

        data = response.json()
        assert "warnings" in data
        assert data["warnings"] is not None
        assert len(data["warnings"]) > 0
        assert any("SohleHoehe Wert ist negative" in warning for warning in data["warnings"])

    def test_optimize_labyrinth_endpoint_invalid_input(self, client):
        request_data = {
            "bottom_level": 2.0,
            "downstream_water_level": 1.0,  # Invalid: below bottom level (UW - Sh <= 0)
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.2,
            "labyrinth_length_max": 8.0,
        }

        response = client.post("/labyrinth/optimize", json=request_data)
        assert response.status_code == 422  # Unprocessable Entity

        data = response.json()
        assert "detail" in data
        assert "message" in data["detail"]
        assert "errors" in data["detail"]

    def test_optimize_labyrinth_endpoint_missing_required_param(self, client):
        request_data = {
            # "bottom_level" is missing
            "downstream_water_level": 1.8,
            "discharge": 20.0,
            "labyrinth_width": 10.0,
            "labyrinth_height": 2.2,
            "labyrinth_length_max": 8.0,
        }

        response = client.post("/labyrinth/optimize", json=request_data)
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert any("bottom_level" in str(error) and "missing" in str(error).lower() for error in data["detail"])
