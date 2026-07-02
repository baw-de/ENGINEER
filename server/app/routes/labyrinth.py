import contextlib
import io
import logging
import os
import tempfile

from fastapi import APIRouter, BackgroundTasks, HTTPException
from starlette.responses import FileResponse

import STL_function
from engineer import EngineerInputError, Labyrinth, optimize_labyrinth_geometry

try:
    # Works when imported as server.app.routes.*
    from server.app.routes.utils.plot_helpers import store_plot_source
except ModuleNotFoundError:
    # Fallback for flatter package layouts.
    from .utils.plot_helpers import store_plot_source
from ..schemas import LabyrinthOptimizeRequest, LabyrinthOptimizeResult, LabyrinthRequest, LabyrinthResult


def _remove_file(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


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

    # Keep latest computed labyrinth object for /plots/labyrinth rendering.
    store_plot_source("labyrinth", labyrinth)

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


@router.post("/stl")
def download_labyrinth_stl(req: LabyrinthRequest, background_tasks: BackgroundTasks) -> FileResponse:
    """
    Generate the labyrinth STL with the provided parameters and stream it back as a download.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".stl")
    temp_file.close()

    try:
        STL_function.generate_labyrinth_geometry(
            D=req.D,
            W=req.labyrinth_width,
            alpha=req.labyrinth_key_angle,
            B=req.labyrinth_length,
            t=req.t,
            P=req.labyrinth_height,
            filename=temp_file.name,
        )
    except Exception as exc:
        _remove_file(temp_file.name)
        logging.getLogger(__name__).error(f"STL generation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=422, detail="STL generation failed with the provided labyrinth parameters.") from exc

    background_tasks.add_task(_remove_file, temp_file.name)
    return FileResponse(
        path=temp_file.name,
        filename="labyrinth_weir.stl",
        media_type="application/octet-stream",
    )


@router.post("/optimize/stl")
def download_optimized_labyrinth_stl(req: LabyrinthOptimizeRequest, background_tasks: BackgroundTasks) -> FileResponse:
    """
    Optimize the labyrinth geometry and stream the resulting STL back as a download.
    """
    captured_output = io.StringIO()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".stl")
    temp_file.close()

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

        # Generate STL with optimized geometry values
        STL_function.generate_labyrinth_geometry(
            D=best_labyrinth.D,
            W=best_labyrinth.W,
            alpha=best_labyrinth.alpha,
            B=best_labyrinth.B,
            t=req.t,
            P=best_labyrinth.P,
            filename=temp_file.name,
        )
    except EngineerInputError as exc:
        _remove_file(temp_file.name)
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Optimization failed due to invalid inputs.",
                "errors": exc.messages,
            },
        ) from exc
    except Exception as exc:
        _remove_file(temp_file.name)
        logging.getLogger(__name__).error(f"Optimized STL generation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=422, detail="STL generation failed for the optimized labyrinth geometry.") from exc

    background_tasks.add_task(_remove_file, temp_file.name)
    return FileResponse(
        path=temp_file.name,
        filename="labyrinth_weir_optimized.stl",
        media_type="application/octet-stream",
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

    # Keep latest optimized labyrinth object for /plots/optimize rendering.
    store_plot_source("optimize", best_labyrinth)

    return LabyrinthOptimizeResult(
        B_best=best_labyrinth.B,
        D_best=best_labyrinth.D,
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
