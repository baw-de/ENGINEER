from typing import List, Optional

from pydantic import BaseModel, Field, confloat


class LabyrinthRequest(BaseModel):
    bottom_level: float = Field(0.1, description="Bottom height [m] (bed level can be negative)")
    downstream_water_level: float = Field(1.09, description="Downstream water level [m]")
    discharge: confloat(gt=0) = Field(10.0, description="Discharge [m³/s]")
    labyrinth_width: confloat(gt=0) = Field(15.0, description="Labyrinth weir width [m]")
    labyrinth_height: confloat(gt=0) = Field(2.2, description="Labyrinth weir height [m]")
    labyrinth_length: confloat(gt=0) = Field(8.0, description="Labyrinth weir length in flow direction [m]")
    labyrinth_key_angle: confloat(gt=0) = Field(8.0, description="Key angle [degree]")
    D: Optional[float] = Field(0.5, description="Front wall width [m]")
    t: Optional[float] = Field(0.3, description="Key wall thickness [m]")

    class Config:
        #prefill the example with the default values
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
    bottom_level: float = Field(0.1, description="Bottom height [m]")
    downstream_water_level: float = Field(1.8, description="Downstream water level at design discharge [m]")
    discharge: confloat(gt=0) = Field(20.0, description="Design discharge [m³/s]")
    labyrinth_width: confloat(gt=0) = Field(10.0, description="Available width for the labyrinth weir [m]")
    labyrinth_height: confloat(gt=0) = Field(2.2, description="Available crest height (design upstream level) [m]")
    labyrinth_length_max: confloat(gt=0) = Field(8.0, description="Available length in flow direction [m]")

    class Config:
        #prefill the example with the default values
        json_schema_extra = {
            "example": {
                "bottom_level": 0.1,
                "downstream_water_level": 1.8,
                "discharge": 20.0,
                "labyrinth_width": 10.0,
                "labyrinth_height": 2.2,
                "labyrinth_length_max": 8.0,
            }
        }


class FlapGateRequest(BaseModel):
    bottom_level: float = Field(0.1, description="Bottom height at flap gate [m]")
    downstream_water_level: float = Field(1.09, description="Downstream water level [m]")
    discharge: confloat(gt=0) = Field(10.0, description="Discharge through flap gate [m³/s]")
    flap_gate_width: confloat(gt=0) = Field(1.4, description="Flap width [m]")
    flap_gate_height: confloat(gt=0) = Field(2.35, description="Flap height [m]")
    flap_gate_angle: float = Field(74.0, description="Flap angle [degree]")

    class Config:
        #prefill the example with the default values
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


class OperationalModelRequest(BaseModel):
    bottom_level: float = Field(..., description="Bottom height [m]")
    downstream_water_level: float = Field(..., description="Downstream water level [m]")
    discharge: confloat(gt=0) = Field(..., description="Reference discharge [m³/s]")
    labyrinth_width: confloat(gt=0) = Field(..., description="Labyrinth weir width [m]")
    labyrinth_height: confloat(gt=0) = Field(..., description="Labyrinth weir height [m]")
    labyrinth_length: confloat(gt=0) = Field(..., description="Labyrinth weir length in flow direction [m]")
    labyrinth_key_angle: confloat(gt=0) = Field(..., description="Key angle [degree]")
    discharge_vector: List[confloat(gt=0)] = Field(..., description="Discharge vector [m³/s]")
    downstream_water_level_vector: List[float] = Field(..., description="Downstream water level vector [m]")
    upstream_water_level_vector: List[float] = Field(..., description="Upstream water level vector [m]")
    interpolation_method: str = Field(
        "exponential",
        description="Interpolation method for hydrograph data ('exponential', 'linear', 'quadratic', 'cubic')",
    )
    flap_gate_bottom_level: float = Field(..., description="Bottom height at flap gate [m]")
    flap_gate_downstream_water_level: float = Field(..., description="Downstream water level at flap gate [m]")
    flap_gate_discharge: confloat(gt=0) = Field(..., description="Discharge through flap gate [m³/s]")
    flap_gate_width: confloat(gt=0) = Field(..., description="Flap gate width [m]")
    flap_gate_height: confloat(gt=0) = Field(..., description="Flap gate height [m]")
    flap_gate_angle: float = Field(..., description="Flap gate angle [degree]")
    design_upstream_water_level: float = Field(..., description="Design upstream water level [m]")
    max_flap_gate_angle: float = Field(..., description="Maximum flap gate angle [degree]")
    fish_body_height: float = Field(..., description="Fish body height for bypass design [m]")

    class Config:
        #prefill the example with the default values
        json_schema_extra = {
            "example": {
                "bottom_level": 0.1,
                "downstream_water_level": 1.8,
                "discharge": 20.0,
                "labyrinth_width": 10.0,
                "labyrinth_height": 2.1,
                "labyrinth_length": 7.7,
                "labyrinth_key_angle": 7.0,
                "discharge_vector": [2.09, 2.79, 6.01, 11.9, 13.9, 16.3, 16.5, 18.6, 20.5, 22.9, 24.5],
                "downstream_water_level_vector": [1.07, 1.15, 1.19, 1.25, 1.38, 1.39, 1.74, 1.74, 1.94, 2.67, 2.67],
                "upstream_water_level_vector": [2.03, 2.15, 2.16, 2.19, 2.22, 2.21, 2.33, 2.33, 2.47, 2.47, 2.47],
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
        }


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
    warnings: Optional[List[str]] = Field(None, description="Warnings, if any")


class LabyrinthOptimizeResult(BaseModel):
    B_best: float = Field(..., description="Optimal key length B [m]")
    Angle_best: float = Field(..., description="Optimal key angle alpha [°]")
    N_best: int = Field(..., description="Optimal number of keys")
    w_best: float = Field(..., description="Optimal key width w [m]")
    l_best: float = Field(..., description="Optimal side wall length l [m]")
    S_best: float = Field(..., description="Optimal straight crest portion S [m]")
    L_best: float = Field(..., description="Optimal total crest length L [m]")
    Hu_best: float = Field(..., description="Minimum upstream head Hu_min [m]")
    Cd_best: float = Field(..., description="Optimal discharge coefficient Cd")
    v_best: float = Field(..., description="Optimal velocity v [m/s]")


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
    warnings: Optional[List[str]] = Field(None, description="Warnings, if any")


class OperationalModelResult(BaseModel):
    results: List["OperationalPoint"] = Field(..., description="Computed series over full discharge range.")
    results_events: List["OperationalPoint"] = Field(..., description="Interpolated results for the input discharge events.")


class OperationalPoint(BaseModel):
    discharge: float = Field(..., description="Discharge Q [m³/s]")
    downstream_water_level: float = Field(..., description="Downstream water level UW [m]")
    upstream_water_level: float = Field(..., description="Upstream water level OW [m]")
    head_over_crest: Optional[float] = Field(
        None, description="Head over crest / upstream head above crest [m] (if available)."
    )
    labyrinth_discharge: float = Field(..., description="Labyrinth discharge share [m³/s].")
    flap_gate_discharge: float = Field(..., description="Flap gate discharge share [m³/s].")
    flap_gate_angle: float = Field(..., description="Flap gate angle alpha [degree] for this discharge.")


