# LABYRINTH API - User Guide

## Local Development / Server Startup

### Prerequisites

- Python 3.9+ installed
- Repository cloned, working directory: project root (`ENGINEER/`)

### Install Dependencies

Navigate to the project root `ENGINEER` folder and set up a virtual environment + dependencies:

```bash
cd ENGINEER
python3 -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Start FastAPI Server Locally

Start (always from the `ENGINEER/` folder):

- **With FastAPI-CLI** (if installed):

```bash
fastapi dev main.py
```

After startup:

- **Base URL:** `http://localhost:8000`
- **Interactive API Documentation:** `http://localhost:8000/docs`

---

## Overview

The LABYRINTH API is a REST API for hydraulic calculations of labyrinth weirs and flap gates. It enables the calculation of hydraulic parameters, optimization of weir geometries, and simulation of operational behavior.

**Base URL:** `http://localhost:8000` (locally) or your server URL

**API Documentation:** Available at `/docs` after starting the server (e.g., `http://localhost:8000/docs`)

---

## Endpoints

### 1. Calculate Labyrinth Weir

**POST** `/labyrinth/compute`

Calculates the hydraulic parameters for a labyrinth weir with given geometry parameters.

#### Request Schema (Input)

| Field                    | Type             | Description                       | Unit     | Required       |
| ------------------------ | ---------------- | --------------------------------- | -------- | -------------- |
| `bottom_level`           | float            | Bottom height                     | m a.s.l. | ✓              |
| `downstream_water_level` | float            | Downstream water level            | m a.s.l. | ✓              |
| `discharge`              | float (>0)       | Discharge                         | m³/s     | ✓              |
| `labyrinth_width`        | float (>0)       | Total width of labyrinth weir     | m        | ✓              |
| `labyrinth_height`       | float (>0)       | Height of labyrinth weir          | m        | ✓              |
| `labyrinth_length`       | float (>0)       | Length of a key in flow direction | m        | ✓              |
| `labyrinth_key_angle`    | float (>0)       | Angle of inclined side walls      | °        | ✓              |
| `D`                      | float (optional) | Front wall thickness              | m        | (Default: 0.3) |
| `t`                      | float (optional) | Wall thickness of keys            | m        | (Default: 0.3) |

#### Response Schema (Output)

| Field          | Type         | Description                     | Unit     |
| -------------- | ------------ | ------------------------------- | -------- |
| **Geometry**   |
| `N`            | int          | Number of keys                  | -        |
| `L`            | float        | Total developed weir length     | m        |
| `w`            | float        | Width of a single key           | m        |
| `l`            | float        | Length of inclined side wall    | m        |
| `S`            | float        | Remaining straight weir length  | m        |
| **Hydraulics** |
| `Hu`           | float        | Upstream energy head            | m        |
| `hu`           | float        | Water level above crest         | m        |
| `yu`           | float        | Upstream water level (absolute) | m a.s.l. |
| `Cd`           | float        | Discharge coefficient           | -        |
| `v`            | float        | Velocity                        | m/s      |
| `hd`           | float        | Tailwater above crest           | m        |
| `Hd`           | float        | Specific energy in tailwater    | m        |
| `rs`           | string       | Backwater influence status      | -        |
| `warnings`     | List[string] | Warnings (if any)               | -        |

#### Example Request

```json
{
  "bottom_level": 0.1,
  "downstream_water_level": 1.09,
  "discharge": 10,
  "labyrinth_width": 15,
  "labyrinth_height": 2.2,
  "labyrinth_length": 8,
  "labyrinth_key_angle": 8,
  "D": 0.5,
  "t": 0.3
}
```

---

### 2. Optimize Labyrinth Weir

**POST** `/labyrinth/optimize`

Finds the optimal geometry of a labyrinth weir for maximum hydraulic capacity under given boundary conditions.

#### Request Schema (Input)

| Field                    | Type       | Description              | Unit     | Required |
| ------------------------ | ---------- | ------------------------ | -------- | -------- |
| `bottom_level`           | float      | Bottom height            | m a.s.l. | ✓        |
| `downstream_water_level` | float      | Downstream water level   | m a.s.l. | ✓        |
| `discharge`              | float (>0) | Design discharge         | m³/s     | ✓        |
| `labyrinth_width`        | float (>0) | Available width          | m        | ✓        |
| `labyrinth_height`       | float (>0) | Available height         | m        | ✓        |
| `labyrinth_length_max`   | float (>0) | Maximum available length | m        | ✓        |

#### Response Schema (Output)

| Field                  | Type  | Description                   | Unit |
| ---------------------- | ----- | ----------------------------- | ---- |
| **Optimal Geometry**   |
| `B_best`               | float | Optimal key length            | m    |
| `Angle_best`           | float | Optimal key angle             | °    |
| `N_best`               | int   | Optimal number of keys        | -    |
| `w_best`               | float | Optimal key width             | m    |
| `l_best`               | float | Optimal side wall length      | m    |
| `S_best`               | float | Optimal straight weir length  | m    |
| `L_best`               | float | Optimal total length          | m    |
| **Optimal Hydraulics** |
| `Hu_best`              | float | Minimum upstream energy head  | m    |
| `Cd_best`              | float | Optimal discharge coefficient | -    |
| `v_best`               | float | Optimal velocity              | m/s  |

#### Example Request

```json
{
  "bottom_level": 0.1,
  "downstream_water_level": 1.8,
  "discharge": 20,
  "labyrinth_width": 10,
  "labyrinth_height": 2.2,
  "labyrinth_length_max": 8
}
```

---

### 3. Calculate Flap Gate

**POST** `/flap/compute`

Calculates the hydraulic parameters for a flap gate (fish-belly flap).

#### Request Schema (Input)

| Field                    | Type       | Description            | Unit     | Required |
| ------------------------ | ---------- | ---------------------- | -------- | -------- |
| `bottom_level`           | float      | Bottom height          | m a.s.l. | ✓        |
| `downstream_water_level` | float      | Downstream water level | m a.s.l. | ✓        |
| `discharge`              | float (>0) | Discharge              | m³/s     | ✓        |
| `flap_gate_width`        | float (>0) | Flap width             | m        | ✓        |
| `flap_gate_height`       | float (>0) | Flap height            | m        | ✓        |
| `flap_gate_angle`        | float      | Angle to vertical      | °        | ✓        |

#### Response Schema (Output)

| Field            | Type         | Description                                    | Unit     |
| ---------------- | ------------ | ---------------------------------------------- | -------- |
| **Geometry**     |
| `P_neu`          | float        | Effective weir height (after angle correction) | m        |
| **Hydraulics**   |
| `mu`             | float        | Discharge coefficient                          | -        |
| `mu_ratio`       | float        | Ratio of discharge coefficients                | -        |
| `hu`             | float        | Upstream water level above crest               | m        |
| `yu`             | float        | Upstream water level (absolute)                | m a.s.l. |
| `hd`             | float        | Tailwater level above crest                    | m        |
| `v`              | float        | Velocity                                       | m/s      |
| `vd`             | float        | Tailwater velocity                             | m/s      |
| `beschleunigung` | float        | Acceleration along the gate                    | m/(s·m)  |
| `h_gr`           | float        | Critical water depth                           | m        |
| `v_gr`           | float        | Critical velocity                              | m/s      |
| `warnings`       | List[string] | Warnings (if any)                              | -        |

#### Example Request

```json
{
  "bottom_level": 0.1,
  "downstream_water_level": 1.09,
  "discharge": 10,
  "flap_gate_width": 1.4,
  "flap_gate_height": 2.35,
  "flap_gate_angle": 74
}
```

---

### 4. Simulate Operational Model

**POST** `/operational-model`

Simulates the operational behavior of a labyrinth weir (optionally with flap gate) over an entire discharge curve.

#### Request Schema (Input)

**Labyrinth Parameters:**

- `bottom_level`, `downstream_water_level`, `discharge` (as above)
- `labyrinth_width`, `labyrinth_height`, `labyrinth_length`, `labyrinth_key_angle`

**Discharge and Water Level Curves:**

- `discharge_vector`: List of discharge values [m³/s]
- `downstream_water_level_vector`: List of downstream water levels [m a.s.l.]
- `upstream_water_level_vector`: List of actual upstream water levels [m a.s.l.]

**Interpolation:**

- `interpolation_method`: "exponential", "linear", "quadratic", "cubic" (Default: "exponential")

**Optional Flap Gate Parameters:**

- `flap_gate_bottom_level`, `flap_gate_downstream_water_level`, `flap_gate_discharge`
- `flap_gate_width`, `flap_gate_height`, `flap_gate_angle`

**Design Parameters (required for flap gate):**

- `design_upstream_water_level`: Design water level [m a.s.l.]
- `max_flap_gate_angle`: Maximum flap gate angle [°]
- `fish_body_height`: Fish body height for bypass design [m]

#### Response Schema (Output)

| Field     | Type   | Description    |
| --------- | ------ | -------------- |
| `message` | string | Status message |
| `status`  | string | Status         |

_Note: Full implementation follows._

#### Example Request

```json
{
  "bottom_level": 0.1,
  "downstream_water_level": 1.09,
  "discharge": 10,
  "labyrinth_width": 15,
  "labyrinth_height": 2.2,
  "labyrinth_length": 8,
  "labyrinth_key_angle": 8,
  "discharge_vector": [2.09, 2.79, 6.01, 11.9],
  "downstream_water_level_vector": [1.07, 1.15, 1.19, 1.25],
  "upstream_water_level_vector": [2.03, 2.15, 2.16, 2.19],
  "interpolation_method": "exponential",
  "flap_gate_bottom_level": 0.1,
  "flap_gate_downstream_water_level": 1.09,
  "flap_gate_discharge": 10,
  "flap_gate_width": 1.4,
  "flap_gate_height": 2.35,
  "flap_gate_angle": 74,
  "design_upstream_water_level": 2.2,
  "max_flap_gate_angle": 90,
  "fish_body_height": 0.4
}
```

---

## Important Notes

- **Units:** All lengths in meters [m], discharges in m³/s, angles in degrees [°]
- **Water Levels:** Absolute values in m a.s.l. (meters above sea level)
- **Optional Parameters:** If not specified, default values are used
- **Validation:** The API automatically validates input values (e.g., discharge > 0)
- **Warnings:** Invalid range limits return warnings in `warnings`

---

## Error Handling

The API returns standard HTTP status codes:

- **`200 OK`**: Successful calculation.
- **`422 Unprocessable Entity`**: Input error.
  - Either Pydantic validation (e.g., missing required fields, wrong types), then `detail` contains the usual FastAPI/Pydantic field details.
  - Or domain validation from the ENGINEER core (`EngineerInputError`), e.g.:
    - negative or implausible hydraulic quantities (discharge, heights, angles),
    - tailwater ≤ bottom (UW - bottom ≤ 0),
    - for `/operational`: empty vectors or vectors with different lengths.
  - In these cases, the endpoints return a `detail` object of the form:
    - Labyrinth / Flap: `{"message": "...", "errors": ["Error 1", "Error 2", ...]}`
    - Operational: `{"message": "Operational model input is invalid.", "errors": [...]}`.
- **`500 Internal Server Error`**: Unexpected server error.
  - For `/operational` a structured JSON is returned:
    `{"message": "Operational model failed due to an internal error.", "error_type": "...", "error": "..."}`.

For validation errors, the response contains details about the invalid fields or a list of domain error messages.
