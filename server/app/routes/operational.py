import numpy as np
from fastapi import APIRouter, HTTPException

from engineer import EngineerInputError, FlapGate, Labyrinth, operational_model

from ..schemas import OperationalModelRequest, OperationalModelResult, OperationalPoint

router = APIRouter()


@router.post("", response_model=OperationalModelResult)
def compute_operational_model(req: OperationalModelRequest) -> OperationalModelResult:
    try:
        # Create base labyrinth object
        labyrinth = Labyrinth(
            bottom_level=req.bottom_level,
            downstream_water_level=req.downstream_water_level,
            discharge=req.discharge,
            labyrinth_width=req.labyrinth_width,
            labyrinth_height=req.labyrinth_height,
            labyrinth_length=req.labyrinth_length,
            labyrinth_key_angle=req.labyrinth_key_angle,
            show_errors=False,
            show_geometry=False,
            show_results=False,
            path="",
        )

        # Flap gate object
        flap_gate = FlapGate(
            bottom_level=req.flap_gate_bottom_level,
            downstream_water_level=req.flap_gate_downstream_water_level,
            discharge=req.flap_gate_discharge,
            flap_gate_width=req.flap_gate_width,
            flap_gate_height=req.flap_gate_height,
            flap_gate_angle=req.flap_gate_angle,
            show_errors=False,
        )

        # Convert vectors to NumPy arrays to match the expectations of the core ENGINEER library
        discharge_vector = np.array(req.discharge_vector, dtype=float)
        downstream_water_level_vector = np.array(req.downstream_water_level_vector, dtype=float)
        upstream_water_level_vector = np.array(req.upstream_water_level_vector, dtype=float)

        # Run the operational model with labyrinth and flap gate objects + input parameters (vector, interpolation method, etc.)
        results_df, results_events_df = operational_model(
            labyrinth_object=labyrinth,
            discharge_vector=discharge_vector,
            downstream_water_level_vector=downstream_water_level_vector,
            upstream_water_level_vector=upstream_water_level_vector,
            interpolation_method=req.interpolation_method,
            flap_gate_opject=flap_gate,
            design_upstream_water_level=req.design_upstream_water_level,
            max_flap_gate_angle=req.max_flap_gate_angle,
            fish_body_height=req.fish_body_height,
            show_plot=False,
            save_plot=False,
            path="",
        )
    except EngineerInputError as exc:
        # Explicitly surface detailed validation messages coming from the ENGINEER core
        raise HTTPException(
            status_code=422,
            detail={"message": "Operational model input is invalid.", "errors": exc.messages},
        ) from exc

    def df_to_points(df):
        points = []
        for row in df.to_dict(orient="records"):
            point = OperationalPoint(
                discharge=row.get("Abfluss"),
                downstream_water_level=row.get("UW"),
                upstream_water_level=row.get("OW"),
                head_over_crest=None,
                labyrinth_discharge=row.get("Labyrinth Q"),
                flap_gate_discharge=row.get("Klappe Q"),
                flap_gate_angle=row.get("Klappe winkel"),
            )
            points.append(point)
        return points

    return OperationalModelResult(results=df_to_points(results_df), results_events=df_to_points(results_events_df))
