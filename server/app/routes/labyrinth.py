import contextlib
import io

from fastapi import APIRouter, HTTPException

from engineer import EngineerInputError, Labyrinth, optimize_labyrinth_geometry

from ..schemas import LabyrinthOptimizeRequest, LabyrinthOptimizeResult, LabyrinthRequest, LabyrinthResult

router = APIRouter()


@router.post("/compute", response_model=LabyrinthResult)
def compute_labyrinth(req: LabyrinthRequest) -> LabyrinthResult:
    """
    Calculate hydraulic indicators for a labyrinth weir using ENGINEER helpers.
    """
    # Capture warnings printed during labyrinth creation
    captured_output = io.StringIO()
    warnings = []

    try:
        with contextlib.redirect_stdout(captured_output):
            labyrinth = Labyrinth(
                bottom_level=req.bottom_level,
                downstream_water_level=req.downstream_water_level,
                discharge=req.discharge,
                labyrinth_width=req.labyrinth_width,
                labyrinth_height=req.labyrinth_height,
                labyrinth_length=req.labyrinth_length,
                labyrinth_key_angle=req.labyrinth_key_angle,
                D=req.D,
                t=req.t,
                show_errors=True,  # Enable warnings to be captured
                show_geometry=False,
                show_results=False,
            )
    except EngineerInputError as exc:
        # Input validation error coming from the core ENGINEER library
        raise HTTPException(
            status_code=422,
            detail={"message": "Invalid labyrinth input parameters.", "errors": exc.messages},
        ) from exc

    # Parse captured warnings (only unique warnings)
    warnings = []
    for line in captured_output.getvalue().strip().split("\n"):
        if line.startswith("[Labyrinth]"):
            warnings.append(line.split(": ", 1)[1])

    # Remove duplicates and add ce_value if present
    warnings = list(set(warnings))
    ce_value = getattr(labyrinth, "ce", None)
    if ce_value and ce_value not in warnings:
        warnings.append(ce_value)

    warnings = warnings or None

    return LabyrinthResult(
        N=labyrinth.N,
        L=labyrinth.L,
        w=labyrinth.w,
        l=labyrinth.l,
        S=labyrinth.S,
        Hu=labyrinth.Hu,
        hu=labyrinth.hu,
        yu=labyrinth.yu,
        Cd=labyrinth.Cd,
        v=labyrinth.v,
        hd=labyrinth.hd,
        Hd=labyrinth.Hd,
        rs=labyrinth.rs,
        warnings=warnings,
    )


@router.post("/optimize", response_model=LabyrinthOptimizeResult)
def optimize_labyrinth(req: LabyrinthOptimizeRequest) -> LabyrinthOptimizeResult:
    """
    Optimize labyrinth geometry for maximum hydraulic capacity.
    """
    # Capture warnings printed during optimization
    captured_output = io.StringIO()

    try:
        with contextlib.redirect_stdout(captured_output):
            best_labyrinth = optimize_labyrinth_geometry(
                labyrinth=Labyrinth,
                sohleHoehe=req.bottom_level,
                UW=req.downstream_water_level,
                Q=req.discharge,
                labyrinthBreite=req.labyrinth_width,
                labyrinthHoehe=req.labyrinth_height,
                labyrinthLaengeMax=req.labyrinth_length_max,
                D=req.D,
                path="",
                show_results=False,
                show_plot=False,
            )
    except EngineerInputError as exc:
        # Input validation error during optimization
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Optimization failed due to invalid inputs.",
                "errors": exc.messages,
            },
        ) from exc

    # Parse captured warnings from optimization (only unique warnings)
    warnings = []
    for line in captured_output.getvalue().strip().split("\n"):
        if line.startswith("[Labyrinth]"):
            warnings.append(line.split(": ", 1)[1])

    # Remove duplicates and add ce_value if present
    warnings = list(set(warnings))
    ce_value = getattr(best_labyrinth, "ce", None)
    if ce_value and ce_value not in warnings:
        warnings.append(ce_value)

    warnings = warnings or None

    return LabyrinthOptimizeResult(
        B_best=best_labyrinth.B,
        Angle_best=best_labyrinth.alpha,
        N_best=best_labyrinth.N,
        w_best=best_labyrinth.w,
        l_best=best_labyrinth.l,
        S_best=best_labyrinth.S,
        L_best=best_labyrinth.L,
        Hu_best=best_labyrinth.Hu,
        Cd_best=best_labyrinth.Cd,
        v_best=best_labyrinth.v,
        warnings=warnings,
    )
