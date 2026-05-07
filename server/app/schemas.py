from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, Field, confloat, field_validator, model_validator

PlotId = Annotated[str, Path(description="Plot identifier (e.g. 'labyrinth' or 'optimize-abc123')")]


class LabyrinthRequest(BaseModel):
    bottom_level: float = Field(..., description="Bottom height [m] (bed level can be negative)")
    downstream_water_level: float = Field(..., description="Downstream water level [m]")
    discharge: confloat(gt=0) = Field(..., description="Discharge [m³/s]")
    labyrinth_width: confloat(gt=0) = Field(..., description="Labyrinth weir width [m]")
    labyrinth_height: confloat(gt=0) = Field(..., description="Labyrinth weir height [m]")
    labyrinth_length: confloat(gt=0) = Field(..., description="Labyrinth weir length in flow direction [m]")
    labyrinth_key_angle: confloat(gt=0) = Field(..., description="Key angle [degree]")
    D: float = Field(0.5, description="Front wall width [m]")
    t: float = Field(0.3, description="Key wall thickness [m]")

    class Config:
        # prefill the example with the default values
        json_schema_extra = {
            "example": {
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
        }


class LabyrinthOptimizeRequest(BaseModel):
    bottom_level: float = Field(..., description="Bottom height [m]")
    downstream_water_level: float = Field(..., description="Downstream water level at design discharge [m]")
    discharge: confloat(gt=0) = Field(..., description="Design discharge [m³/s]")
    labyrinth_width: confloat(gt=0) = Field(..., description="Available width for the labyrinth weir [m]")
    labyrinth_height: confloat(gt=0) = Field(..., description="Available crest height (design upstream level) [m]")
    labyrinth_length_max: confloat(gt=0) = Field(..., description="Available length in flow direction [m]")
    D: float = Field(0.5, description="Front wall width used for optimization [m]")

    class Config:
        # prefill the example with the default values
        json_schema_extra = {
            "example": {
                "bottom_level": 0.1,
                "downstream_water_level": 1.8,
                "discharge": 20.0,
                "labyrinth_width": 10.0,
                "labyrinth_height": 2.2,
                "labyrinth_length_max": 8.0,
                "D": 0.5,
            }
        }


class FlapGateRequest(BaseModel):
    bottom_level: float = Field(..., description="Bottom height at flap gate [m]")
    downstream_water_level: float = Field(..., description="Downstream water level [m]")
    discharge: confloat(gt=0) = Field(..., description="Discharge through flap gate [m³/s]")
    flap_gate_width: confloat(gt=0) = Field(..., description="Flap width [m]")
    flap_gate_height: confloat(gt=0) = Field(..., description="Flap height [m]")
    flap_gate_angle: float = Field(..., description="Flap angle [degree]")

    class Config:
        # prefill the example with the default values
        json_schema_extra = {
            "example": {
                "bottom_level": 0.1,
                "downstream_water_level": 1.09,
                "discharge": 10.0,
                "flap_gate_width": 1.4,
                "flap_gate_height": 2.35,
                "flap_gate_angle": 74.0,
            }
        }

    @field_validator("flap_gate_angle")
    def flap_gate_angle_range(cls, value):
        if not 0 <= value <= 90:
            raise ValueError("Klappenwinkel β muss im Bereich 0° ≤ β ≤ 90° liegen.")
        return value


class OperationalModelRequest(BaseModel):
    bottom_level: float = Field(..., description="Bottom height [m]")
    downstream_water_level: float = Field(..., description="Downstream water level [m]")
    discharge: confloat(gt=0) = Field(..., description="Reference discharge [m³/s]")
    labyrinth_width: confloat(gt=0) = Field(..., description="Labyrinth weir width [m]")
    labyrinth_height: confloat(gt=0) = Field(..., description="Labyrinth weir height [m]")
    labyrinth_length: confloat(gt=0) = Field(..., description="Labyrinth weir length in flow direction [m]")
    labyrinth_key_angle: confloat(gt=0) = Field(..., description="Key angle [degree]")
    D: float = Field(0.5, description="Front wall width [m]")
    discharge_vector: list[confloat(gt=0)] = Field(..., description="Discharge vector [m³/s]")
    downstream_water_level_vector: list[float] = Field(..., description="Downstream water level vector [m]")
    interpolation_method: str = Field(
        "exponential",
        description="Interpolation method for hydrograph data ('exponential', 'linear', 'quadratic', 'cubic')",
    )
    interpolation_stepsize: float = Field(
        1,
        gt=0,
        description="Step size for interpolating discharge range [m³/s].",
    )
    flap_gate_bottom_level: float | None = Field(None, description="Bottom height at flap gate [m]")
    flap_gate_downstream_water_level: float | None = Field(
        None,
        description="Downstream water level at flap gate [m]",
    )
    flap_gate_discharge: confloat(gt=0) | None = Field(None, description="Discharge through flap gate [m³/s]")
    flap_gate_width: confloat(gt=0) | None = Field(None, description="Flap gate width [m]")
    flap_gate_height: confloat(gt=0) | None = Field(None, description="Flap gate height [m]")
    flap_gate_angle: float | None = Field(None, description="Flap gate angle [degree]")
    design_upstream_water_level: float = Field(..., description="Design upstream water level [m]")
    max_flap_gate_angle: float | None = Field(
        None,
        description="Maximum flap gate angle [degree]",
    )
    fish_body_height: float = Field(..., description="Fish body height for bypass design [m]")
    include_flap_gate: bool = Field(
        ...,
        description="Whether the operational model should account for the flap gate.",
    )

    class Config:
        # prefill the example with the default values
        json_schema_extra = {
            "example": {
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
                "include_flap_gate": True,
                "interpolation_stepsize": 1,
                "design_upstream_water_level": 2.2,
                "max_flap_gate_angle": 90.0,
                "fish_body_height": 0.4,
            }
        }

    @field_validator("flap_gate_angle", "max_flap_gate_angle")
    def flap_gate_angles_range(cls, value, info):
        if value is None:
            return value
        if not 0 <= value <= 90:
            if info.field_name == "flap_gate_angle":
                raise ValueError("Klappenwinkel β muss im Bereich 0° ≤ β ≤ 90° liegen.")
            raise ValueError("Maximaler Klappenwinkel (β) muss im Bereich 0° ≤ β ≤ 90° liegen.")
        return value

    @model_validator(mode="after")
    def flap_gate_values_presence(cls, values):
        include_flap_gate = getattr(values, "include_flap_gate", True)
        if not include_flap_gate:
            return values
        mandatory_fields = [
            "flap_gate_bottom_level",
            "flap_gate_downstream_water_level",
            "flap_gate_discharge",
            "flap_gate_width",
            "flap_gate_height",
            "flap_gate_angle",
            "max_flap_gate_angle",
        ]
        missing = [name for name in mandatory_fields if getattr(values, name) is None]
        if missing:
            raise ValueError(f"Flap gate fields required when include_flap_gate is true: {missing}")
        return values


class LabyrinthResult(BaseModel):
    N: int = Field(..., description="Number of keys")
    L: float = Field(..., description="Total developed crest length L [m]")
    w: float = Field(..., description="Width of a single key [m]")
    l: float = Field(..., description="Length of the inclined side wall [m]")
    S: float = Field(..., description="Remaining straight crest length S [m]")
    Hu: float = Field(..., description="Upstream head Hu [m]")
    hu: float = Field(..., description="Water level above crest hu [m]")
    yu: float = Field(..., description="Upstream water level yu [m a.s.l.]")
    Cd: float = Field(..., description="Discharge coefficient Cd [-]")
    v: float = Field(..., description="Velocity v [m/s]")
    hd: float = Field(..., description="Tailwater above crest hd [m]")
    Hd: float = Field(..., description="Specific energy in tailwater Hd [m]")
    rs: str = Field(..., description="Backwater status message")
    warnings: list[str] | None = Field(None, description="Warnings, if any")


class LabyrinthOptimizeResult(BaseModel):
    B_best: float = Field(..., description="Optimal key length B [m]")
    D_best: float = Field(..., description="Optimal front wall width D [m]")
    Angle_best: float = Field(..., description="Optimal key angle alpha [°]")
    N_best: int = Field(..., description="Optimal number of keys")
    w_best: float = Field(..., description="Optimal key width w [m]")
    l_best: float = Field(..., description="Optimal side wall length l [m]")
    S_best: float = Field(..., description="Optimal straight crest portion S [m]")
    L_best: float = Field(..., description="Optimal total crest length L [m]")
    Hu_best: float = Field(..., description="Minimum upstream head Hu_min [m]")
    Cd_best: float = Field(..., description="Optimal discharge coefficient Cd")
    v_best: float = Field(..., description="Optimal velocity v [m/s]")
    warnings: list[str] | None = Field(None, description="List of warnings generated during optimization")


class FlapGateResult(BaseModel):
    P_neu: float = Field(..., description="Effective sill height P_neu [m]")
    mu: float = Field(..., description="Discharge coefficient mu [-]")
    mu_ratio: float = Field(..., description="Ratio of discharge coefficients mu_ratio [-]")
    hu: float = Field(..., description="Upstream water level above crest hu [m]")
    yu: float = Field(..., description="Upstream water level yu [m a.s.l.]")
    hd: float = Field(..., description="Tailwater level above crest hd [m]")
    v: float = Field(..., description="Velocity v [m/s]")
    vd: float = Field(..., description="Tailwater velocity vd [m/s]")
    beschleunigung: float = Field(..., description="Acceleration along the gate [m/(s·m)]")
    h_gr: float = Field(..., description="Critical depth h_gr [m]")
    v_gr: float = Field(..., description="Critical velocity v_gr [m/s]")
    warnings: list[str] | None = Field(None, description="Warnings, if any")


class OperationalModelResult(BaseModel):
    results: list["OperationalPoint"] = Field(..., description="Computed series over full discharge range.")
    results_events: list["OperationalPoint"] = Field(..., description="Interpolated results for the input discharge events.")
    warnings: list[str] | None = Field(None, description="Warnings generated during computation")


class OperationalPoint(BaseModel):
    discharge: float = Field(..., description="Discharge Q [m³/s]")
    downstream_water_level: float = Field(..., description="Downstream water level UW [m]")
    upstream_water_level: float = Field(..., description="Upstream water level OW [m]")
    labyrinth_head_over_crest: float | None = Field(None, description="Labyrinth-specific head over crest (if available)")
    flap_gate_head_over_crest: float | None = Field(None, description="Flap gate-specific head over crest (if available)")
    labyrinth_discharge: float = Field(..., description="Labyrinth discharge share [m³/s].")
    flap_gate_discharge: float | None = Field(None, description="Flap gate discharge share [m³/s].")
    flap_gate_angle: float | None = Field(
        None,
        description="Flap gate angle alpha [degree] for this discharge.",
    )
