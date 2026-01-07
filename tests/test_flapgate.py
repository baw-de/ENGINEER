import os
import pytest
from fastapi.testclient import TestClient

os.environ["SERVER_MODE"] = "1"

from engineer import FlapGate
from server.app.main import app


class TestFlapGateClass:
    def test_flapgate_initialization_and_computation(self):
        flapgate = FlapGate(
            bottom_level=0.1,
            downstream_water_level=1.09,
            discharge=10.0,
            flap_gate_width=1.4,
            flap_gate_height=2.35,
            flap_gate_angle=74.0,
        )

        # Check that input parameters are set
        assert flapgate.Sh == 0.1
        assert flapgate.UW == 1.09
        assert flapgate.Q == 10.0
        assert flapgate.KW == 1.4
        assert flapgate.KP == 2.35
        assert flapgate.Kalpha == 74.0

        # Check that computed values are set
        assert hasattr(flapgate, "P_neu")
        assert hasattr(flapgate, "mu")  # Discharge coefficient for flap gate
        assert hasattr(flapgate, "mu_ratio")
        assert hasattr(flapgate, "hu")
        assert hasattr(flapgate, "yu")
        assert hasattr(flapgate, "hd")
        assert hasattr(flapgate, "v")
        assert hasattr(flapgate, "vd")
        assert hasattr(flapgate, "beschleunigung")
        assert hasattr(flapgate, "h_gr")
        assert hasattr(flapgate, "v_gr")

        # Check that computed values are reasonable
        assert flapgate.P_neu > 0
        assert flapgate.mu > 0
        assert flapgate.hu > 0
        assert flapgate.v > 0

    def test_flapgate_with_missing_parameters(self):
        flapgate = FlapGate(
            bottom_level=0.1,
            discharge=10.0,
            # downstream_water_level is missing
        )

        # Check that some attributes are set and some are None
        assert flapgate.Sh == 0.1
        assert flapgate.UW is None
        assert flapgate.Q == 10.0

        # Other attributes should not be computed yet
        assert not hasattr(flapgate, "mu")

        # Now update with remaining parameters
        flapgate.UW = 1.09
        flapgate.KW = 1.4
        flapgate.KP = 2.35
        flapgate.Kalpha = 74.0
        flapgate.update()

        # Now computed values should exist
        assert hasattr(flapgate, "mu")

    def test_flapgate_input_validation_errors(self):
        # Test with invalid height (KP < 0.3)
        flapgate_small_height = FlapGate(
            bottom_level=0.1,
            downstream_water_level=1.09,
            discharge=10.0,
            flap_gate_width=1.4,
            flap_gate_height=0.2,  # Too small
            flap_gate_angle=74.0,
            show_errors=True,
        )
        flapgate_small_height.check_for_error()
        assert "außerhalb" in flapgate_small_height.ce

        # Test with extremely small discharge
        flapgate_small_discharge = FlapGate(
            bottom_level=0.1,
            downstream_water_level=1.09,
            discharge=0.001,  # Very small
            flap_gate_width=1.4,
            flap_gate_height=2.35,
            flap_gate_angle=74.0,
            show_errors=True,
        )
        flapgate_small_discharge.check_for_error()
        # Should trigger error due to hu being out of range


class TestFlapGateAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_compute_flapgate_endpoint(self, client):
        request_data = {"bottom_level": 0.1, "downstream_water_level": 1.09, "discharge": 10.0, "flap_gate_width": 1.4, "flap_gate_height": 2.35, "flap_gate_angle": 74.0}

        response = client.post("/flap/compute", json=request_data)
        assert response.status_code == 200

        data = response.json()
        expected_fields = ["P_neu", "mu", "mu_ratio", "hu", "yu", "hd", "v", "vd", "beschleunigung", "h_gr", "v_gr", "warnings"]

        for field in expected_fields:
            assert field in data

        assert data["P_neu"] > 0
        assert data["mu"] > 0
        assert data["hu"] > 0
        assert data["v"] > 0

    def test_compute_flapgate_endpoint_with_warnings(self, client):
        request_data = {
            "bottom_level": -10.0,  # Invalid: negative (generates warning)
            "downstream_water_level": 1.09,
            "discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": 74.0,
        }

        response = client.post("/flap/compute", json=request_data)
        assert response.status_code == 200  # Should succeed but with warnings

        data = response.json()
        assert "warnings" in data
        assert data["warnings"] is not None
        assert len(data["warnings"]) > 0
        assert any("SohleHoehe Wert ist negative" in warning for warning in data["warnings"])

    def test_compute_flapgate_endpoint_invalid_input(self, client):
        request_data = {
            "bottom_level": 2.0,
            "downstream_water_level": 1.0,  # Invalid: below bottom level (UW - Sh <= 0)
            "discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": 74.0,
        }

        response = client.post("/flap/compute", json=request_data)
        assert response.status_code == 422  # Unprocessable Entity

        data = response.json()
        assert "detail" in data
        assert "message" in data["detail"]
        assert "errors" in data["detail"]

    def test_compute_flapgate_endpoint_missing_required_param(self, client):
        request_data = {
            # "bottom_level" is missing
            "downstream_water_level": 1.09,
            "discharge": 10.0,
            "flap_gate_width": 1.4,
            "flap_gate_height": 2.35,
            "flap_gate_angle": 74.0,
        }

        response = client.post("/flap/compute", json=request_data)
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert any("bottom_level" in str(error) and "missing" in str(error).lower() for error in data["detail"])
