from fastapi import APIRouter, HTTPException

from engineer import EngineerInputError, Labyrinth, optimize_labyrinth_geometry
from ..schemas import (
    LabyrinthOptimizeRequest,
    LabyrinthOptimizeResult,
    LabyrinthRequest,
    LabyrinthResult,
)

router = APIRouter()


@router.post("/compute", response_model=LabyrinthResult)
def compute_labyrinth(req: LabyrinthRequest) -> LabyrinthResult:
    """
    Calculate hydraulic indicators for a labyrinth weir using ENGINEER helpers.
    """
    try:
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
            show_errors=False,
            show_geometry=False,
            show_results=False,
        )
    except EngineerInputError as exc:
        # Input validation error coming from the core ENGINEER library
        raise HTTPException(
            status_code=422,
            detail={"message": "Invalid labyrinth input parameters.", "errors": exc.messages},
        ) from exc

    warnings = None
    ce_value = getattr(labyrinth, "ce", None)
    if ce_value:
        warnings = [ce_value]

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
    try:
        best_labyrinth = optimize_labyrinth_geometry(
            labyrinth=Labyrinth,
            sohleHoehe=req.bottom_level,
            UW=req.downstream_water_level,
            Q=req.discharge,
            labyrinthBreite=req.labyrinth_width,
            labyrinthHoehe=req.labyrinth_height,
            labyrinthLaengeMax=req.labyrinth_length_max,
            path="",
            show_results=False,
            show_plot=False,
        )
    except EngineerInputError as exc:
        # Input validation error during optimization
        raise HTTPException(
            status_code=422,
            detail={"message": "Optimization failed due to invalid inputs.", "errors": exc.messages},
        ) from exc

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
    )

