import io
import contextlib
from fastapi import APIRouter, HTTPException

from engineer import EngineerInputError, FlapGate

from ..schemas import FlapGateRequest, FlapGateResult

router = APIRouter()


@router.post("/compute", response_model=FlapGateResult)
def compute_flap_gate(req: FlapGateRequest) -> FlapGateResult:
    """
    Calculate hydraulic indicators for a flap gate using ENGINEER helpers.
    """
    # Capture warnings printed during flap gate creation
    captured_output = io.StringIO()

    try:
        with contextlib.redirect_stdout(captured_output):
            flap_gate = FlapGate(
                bottom_level=req.bottom_level,
                downstream_water_level=req.downstream_water_level,
                discharge=req.discharge,
                flap_gate_width=req.flap_gate_width,
                flap_gate_height=req.flap_gate_height,
                flap_gate_angle=req.flap_gate_angle,
                show_errors=True,  # Enable warnings to be captured
            )
    except EngineerInputError as exc:
        # Input validation error coming from the core ENGINEER library
        raise HTTPException(
            status_code=422,
            detail={"message": "Invalid flap gate input parameters.", "errors": exc.messages},
        ) from exc

    # Parse captured warnings (only unique warnings)
    warnings = []
    for line in captured_output.getvalue().strip().split("\n"):
        if line.startswith("[FlapGate]"):
            warnings.append(line.split(": ", 1)[1])

    # Remove duplicates and add ce_value if present
    warnings = list(set(warnings))
    ce_value = getattr(flap_gate, "ce", None)
    if ce_value and ce_value != "No errors" and ce_value not in warnings:
        warnings.append(ce_value)

    warnings = warnings or None

    return FlapGateResult(
        P_neu=flap_gate.P_neu,
        mu=flap_gate.mu,
        mu_ratio=flap_gate.mu_ratio,
        hu=flap_gate.hu,
        yu=flap_gate.yu,
        hd=flap_gate.hd,
        v=flap_gate.v,
        vd=flap_gate.vd,
        beschleunigung=flap_gate.beschleunigung,
        h_gr=flap_gate.h_gr,
        v_gr=flap_gate.v_gr,
        warnings=warnings,
    )
