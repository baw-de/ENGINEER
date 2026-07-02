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

### 0. Health Check

**GET** `/health`

Returns the system status. Useful for automated monitoring and uptime checks.

#### Response Schema (Output)

| Field    | Type   | Description            |
| -------- | ------ | ---------------------- |
| `status` | string | Returns `"ok"`         |

#### Example Request

```json
{
  "status": "ok"
}
```

---

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

| Field                    | Type       | Description                           | Unit     | Required |
| ------------------------ | ---------- | ------------------------------------- | -------- | -------- |
| `bottom_level`           | float      | Bottom height                         | m a.s.l. | ✓        |
| `downstream_water_level` | float      | Downstream water level                | m a.s.l. | ✓        |
| `discharge`              | float (>0) | Design discharge                       | m³/s     | ✓        |
| `labyrinth_width`        | float (>0) | Available width                       | m        | ✓        |
| `labyrinth_height`       | float (>0) | Available height                      | m        | ✓        |
| `labyrinth_length_max`   | float (>0) | Maximum available length              | m        | ✓        |
| `D`                      | float      | Front wall width used in optimization | m        | ✗ (default 0.5) |
| `t`                      | float      | Wall thickness for STL generation     | m        | ✗ (default 0.3) |

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
  "labyrinth_length_max": 8,
  "D": 0.5,
  "t": 0.3
}
```

---

### 3. Download Optimized Labyrinth STL

**POST** `/labyrinth/optimize/stl`

Optimizes the labyrinth geometry for the given boundary conditions and streams back an STL generated from the optimized geometry.

#### Request Schema (Input)

Same as `/labyrinth/optimize`, plus the STL-specific wall thickness parameter `t`.

#### Response Schema (Output)

| Field       | Type   | Description                                         |
| ----------- | ------ | --------------------------------------------------- |
| `file`      | binary | Binary STL payload (`Content-Disposition: attachment`) |

The endpoint returns `200 OK` with a binary stream. Invalid geometries produce `422 Unprocessable Entity` with the domain validation message.

#### Example Request

```json
{
  "bottom_level": 0.1,
  "downstream_water_level": 1.8,
  "discharge": 20,
  "labyrinth_width": 10,
  "labyrinth_height": 2.2,
  "labyrinth_length_max": 8,
  "D": 0.5,
  "t": 0.3
}
```

---

### 4. Download Labyrinth STL

**POST** `/labyrinth/stl`

Generates a watertight STL mesh of the labyrinth geometry based on the provided dimensions and streams it back as a file download.

#### Request Schema (Input)

Same as `/labyrinth/compute`:

| Field                    | Type             | Description                       | Unit     | Required       |
| ------------------------ | ---------------- | --------------------------------- | -------- | -------------- |
| `bottom_level`           | float            | Bottom height                     | m a.s.l. | ✓              |
| `downstream_water_level` | float            | Downstream water level            | m a.s.l. | ✓              |
| `discharge`              | float (>0)       | Discharge                         | m³/s     | ✓              |
| `labyrinth_width`        | float (>0)       | Total width of labyrinth weir     | m        | ✓              |
| `labyrinth_height`       | float (>0)       | Height of labyrinth weir          | m        | ✓              |
| `labyrinth_length`       | float (>0)       | Length of a key in flow direction | m        | ✓              |
| `labyrinth_key_angle`    | float (>0)       | Angle of inclined side walls      | °        | ✓              |
| `D`                      | float (optional) | Front wall thickness              | m        | (Default: 0.5) |
| `t`                      | float (optional) | Wall thickness of keys            | m        | (Default: 0.3) |

#### Response Schema (Output)

| Field       | Type   | Description                                         |
| ----------- | ------ | --------------------------------------------------- |
| `file`      | binary | Binary STL payload (`Content-Disposition: attachment`) |

The endpoint returns `200 OK` with a binary stream. Invalid geometries produce `422 Unprocessable Entity` with the domain validation message.

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

### 4. Calculate Flap Gate

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

### 5. Simulate Operational Model

**POST** `/operational`

Simulates the operational behavior of a labyrinth weir (optionally including a flap gate) over a discharge curve and returns both the interpolated curve and the event-based points that were provided.

#### Request Schema (Input)

| Field                             | Type                | Description                                                                 | Unit     | Required |
| --------------------------------- | ------------------- | --------------------------------------------------------------------------- | -------- | -------- |
| `bottom_level`                    | float               | Bottom height                                                               | m a.s.l. | ✓        |
| `downstream_water_level`          | float               | Downstream water level                                                      | m a.s.l. | ✓        |
| `discharge`                       | float (>0)          | Reference discharge                                                         | m³/s     | ✓        |
| `labyrinth_width`                 | float (>0)          | Total width of the labyrinth weir                                           | m        | ✓        |
| `labyrinth_height`                | float (>0)          | Height of the labyrinth weir                                                | m        | ✓        |
| `labyrinth_length`                | float (>0)          | Length of the labyrinth key in flow direction                               | m        | ✓        |
| `labyrinth_key_angle`             | float (>0)          | Key angle of the labyrinth weir                                             | °        | ✓        |
| `D`                               | float               | Front wall thickness (same meaning as other labyrinth endpoints)           | m        | ✗ (default: 0.5) |
| `discharge_vector`                | List[float (>0)] (max 500) | Discharge curve that will be interpolated                                   | m³/s     | ✓        |
| `downstream_water_level_vector`   | List[float] (max 500)      | Water level history that matches the discharge vector                       | m a.s.l. | ✓        |
| `interpolation_method`            | string              | Interpolation method for the hydrograph (`exponential`, `linear`, `quadratic`, `cubic`) | -      | ✗ (default: `"exponential"`) |
| `interpolation_stepsize`          | float (>0, ≤100)           | Discharge stepsize used when filling the computed curve                     | m³/s     | ✗ (default: 1) |
| `include_flap_gate`               | bool                | Whether to include the flap gate hydraulics in the simulation               | -        | ✓        |
| `flap_gate_bottom_level`          | float               | Flap gate sill bottom level (required if `include_flap_gate` is `true`)     | m        | conditional |
| `flap_gate_downstream_water_level` | float               | Flap gate downstream water level (required if `include_flap_gate` is `true`) | m        | conditional |
| `flap_gate_discharge`             | float (>0)          | Discharge through the flap gate (required if `include_flap_gate` is `true`)  | m³/s     | conditional |
| `flap_gate_width`                 | float (>0)          | Flap gate width (required if `include_flap_gate` is `true`)                 | m        | conditional |
| `flap_gate_height`                | float (>0)          | Flap gate height (required if `include_flap_gate` is `true`)                | m        | conditional |
| `flap_gate_angle`                 | float               | Flap gate angle (required if `include_flap_gate` is `true`)                 | °        | conditional |
| `design_upstream_water_level`     | float               | Design upstream water level for flap gate control                          | m a.s.l. | ✓        |
| `max_flap_gate_angle`             | float               | Maximum allowed flap gate angle                                            | °        | ✓        |
| `fish_body_height`                | float               | Height of the fish body used for bypass flow design                         | m        | ✓        |

> **Note:** When `include_flap_gate` is `false`, the flap gate-specific fields may be omitted; when it is `true`, they are required and the `max_flap_gate_angle` / `design_upstream_water_level` / `fish_body_height` fields must also be supplied.

#### Response Schema (Output)

| Field          | Type                     | Description                                                        |
| -------------- | ------------------------ | ------------------------------------------------------------------ |
| `results`      | List[`OperationalPoint`] | Full interpolated discharge curve over the range defined by `discharge_vector` |
| `results_events` | List[`OperationalPoint`] | Interpolated points that correspond to the original discharge events |
| `warnings`     | List[string] \| `null`   | Optional validation or domain warnings                              |

**OperationalPoint**

| Field                       | Type     | Description                                                  |
| --------------------------- | -------- | ------------------------------------------------------------ |
| `discharge`                 | float    | Discharge at this point                                       |
| `downstream_water_level`    | float    | Downstream water level at the same point                      |
| `upstream_water_level`      | float    | Upstream water level computed for this discharge             |
| `labyrinth_head_over_crest` | float \| `null` | Computed head above crest for the labyrinth curve             |
| `flap_gate_head_over_crest`  | float \| `null` | Computed head above crest for the flap gate (if present)     |
| `labyrinth_discharge`       | float    | Portion of discharge through the labyrinth (plain result for `results_events`) |
| `flap_gate_discharge`       | float \| `null` | Portion of discharge passing through the flap gate             |
| `flap_gate_angle`           | float \| `null` | Flap gate angle at this discharge (if flap gate is included) |

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
  "discharge_vector": [2.09, 2.79, 6.01, 11.9, 13.9, 16.3, 16.5, 18.6, 20.5, 22.9, 24.5],
  "downstream_water_level_vector": [1.07, 1.15, 1.19, 1.25, 1.38, 1.39, 1.74, 1.74, 1.94, 2.67, 2.67],
  "interpolation_method": "exponential",
  "interpolation_stepsize": 1,
  "include_flap_gate": true,
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

### 6. Retrieve Geometry Plot

**GET** `/plots/{plot_id}`

Returns the cached SVG plot for the requested `plot_id` (e.g., `labyrinth` or `optimize-abc123`). Successful responses include caching headers and inline filename hints.

#### Path Parameters

| Field     | Type   | Description                                 |
| --------- | ------ | ------------------------------------------- |
| `plot_id`  | string | Plot identifier (must match a stored plot)  |

#### Responses

| Status | Description                                  | Content Type     |
| ------ | -------------------------------------------- | ---------------- |
| 200    | SVG plot image                               | `image/svg+xml`  |
| 404    | Plot is missing or expired                    | `application/json` |
| 500    | Server error during plot generation           | `application/json` |

Example:

```
GET /plots/labyrinth
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
