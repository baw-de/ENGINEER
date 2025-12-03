# LABYRINTH API - Benutzeranleitung

## Lokale Entwicklung / Serverstart

### Voraussetzungen

- Python 3.9+ installiert
- Repository geklont, Arbeitsverzeichnis: Projekt-Root (`ENGINEER/`)

### Abhängigkeiten installieren

Im Projekt-Root in den `ENGINEER`-Ordner wechseln und ein virtuelles Environment + Dependencies installieren:

```bash
cd ENGINEER
python -m venv .venv
source .venv/bin/activate  # unter Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### FastAPI-Server lokal starten

Es gibt zwei empfohlene Varianten (immer aus dem Ordner `ENGINEER/`):

- **Mit FastAPI-CLI** (falls installiert):

```bash
fastapi dev main.py
```

Nach dem Start:

- **Base URL:** `http://localhost:8000`
- **Interaktive API-Dokumentation:** `http://localhost:8000/docs`

---

## Übersicht

Die LABYRINTH API ist eine REST-API zur hydraulischen Berechnung von Labyrinth-Wehren und Klappenwehren. Sie ermöglicht die Berechnung hydraulischer Kennwerte, die Optimierung von Wehrgeometrien und die Simulation des Betriebsverhaltens.

**Base URL:** `http://localhost:8000` (lokal) oder Ihre Server-URL

**API-Dokumentation:** Nach dem Starten des Servers unter `/docs` verfügbar (z.B. `http://localhost:8000/docs`)

---

## Endpunkte

### 1. Labyrinth-Wehr berechnen

**POST** `/labyrinth/compute`

Berechnet die hydraulischen Kennwerte für ein Labyrinth-Wehr mit gegebenen Geometrieparametern.

#### Request Schema (Eingabe)

| Feld                     | Typ              | Beschreibung                      | Einheit  | Pflicht        |
| ------------------------ | ---------------- | --------------------------------- | -------- | -------------- |
| `bottom_level`           | float            | Sohlhöhe                          | m ü. NHN | ✓              |
| `downstream_water_level` | float            | Unterwasserstand                  | m ü. NHN | ✓              |
| `discharge`              | float (>0)       | Abfluss                           | m³/s     | ✓              |
| `labyrinth_width`        | float (>0)       | Gesamtbreite des Labyrinth-Wehrs  | m        | ✓              |
| `labyrinth_height`       | float (>0)       | Höhe des Labyrinth-Wehrs          | m        | ✓              |
| `labyrinth_length`       | float (>0)       | Länge eines Keys in Fließrichtung | m        | ✓              |
| `labyrinth_key_angle`    | float (>0)       | Winkel der schrägen Seitenwände   | °        | ✓              |
| `D`                      | float (optional) | Dicke der Stirnwand               | m        | (Default: 0.3) |
| `t`                      | float (optional) | Wandstärke der Keys               | m        | (Default: 0.3) |

#### Response Schema (Ausgabe)

| Feld          | Typ          | Beschreibung                       | Einheit  |
| ------------- | ------------ | ---------------------------------- | -------- |
| **Geometrie** |
| `N`           | int          | Anzahl der Keys                    | -        |
| `L`           | float        | Gesamte entwickelte Wehrlänge      | m        |
| `w`           | float        | Breite eines einzelnen Keys        | m        |
| `l`           | float        | Länge der schrägen Seitenwand      | m        |
| `S`           | float        | Verbleibende gerade Wehrlänge      | m        |
| **Hydraulik** |
| `Hu`          | float        | Oberwasser-Energiehöhe             | m        |
| `hu`          | float        | Wasserstand über Wehrkrone         | m        |
| `yu`          | float        | Oberwasserstand (absolut)          | m ü. NHN |
| `Cd`          | float        | Abflussbeiwert                     | -        |
| `v`           | float        | Geschwindigkeit                    | m/s      |
| `hd`          | float        | Unterwasser über Wehrkrone         | m        |
| `Hd`          | float        | Spezifische Energie im Unterwasser | m        |
| `rs`          | string       | Rückstaueinfluss-Status            | -        |
| `warnings`    | List[string] | Warnungen (falls vorhanden)        | -        |

#### Beispiel Request

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

### 2. Labyrinth-Wehr optimieren

**POST** `/labyrinth/optimize`

Findet die optimale Geometrie eines Labyrinth-Wehrs für maximale hydraulische Kapazität bei gegebenen Randbedingungen.

#### Request Schema (Eingabe)

| Feld                     | Typ        | Beschreibung              | Einheit  | Pflicht |
| ------------------------ | ---------- | ------------------------- | -------- | ------- |
| `bottom_level`           | float      | Sohlhöhe                  | m ü. NHN | ✓       |
| `downstream_water_level` | float      | Unterwasserstand          | m ü. NHN | ✓       |
| `discharge`              | float (>0) | Bemessungsabfluss         | m³/s     | ✓       |
| `labyrinth_width`        | float (>0) | Verfügbare Breite         | m        | ✓       |
| `labyrinth_height`       | float (>0) | Verfügbare Höhe           | m        | ✓       |
| `labyrinth_length_max`   | float (>0) | Maximale verfügbare Länge | m        | ✓       |

#### Response Schema (Ausgabe)

| Feld                   | Typ   | Beschreibung                    | Einheit |
| ---------------------- | ----- | ------------------------------- | ------- |
| **Optimale Geometrie** |
| `B_best`               | float | Optimale Key-Länge              | m       |
| `Angle_best`           | float | Optimaler Key-Winkel            | °       |
| `N_best`               | int   | Optimale Anzahl Keys            | -       |
| `w_best`               | float | Optimale Key-Breite             | m       |
| `l_best`               | float | Optimale Seitenwand-Länge       | m       |
| `S_best`               | float | Optimale gerade Wehrlänge       | m       |
| `L_best`               | float | Optimale Gesamtlänge            | m       |
| **Optimale Hydraulik** |
| `Hu_best`              | float | Minimale Oberwasser-Energiehöhe | m       |
| `Cd_best`              | float | Optimaler Abflussbeiwert        | -       |
| `v_best`               | float | Optimale Geschwindigkeit        | m/s     |

#### Beispiel Request

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

### 3. Klappenwehr berechnen

**POST** `/flap/compute`

Berechnet die hydraulischen Kennwerte für ein Klappenwehr (Fischbauchklappe).

#### Request Schema (Eingabe)

| Feld                     | Typ        | Beschreibung          | Einheit  | Pflicht |
| ------------------------ | ---------- | --------------------- | -------- | ------- |
| `bottom_level`           | float      | Sohlhöhe              | m ü. NHN | ✓       |
| `downstream_water_level` | float      | Unterwasserstand      | m ü. NHN | ✓       |
| `discharge`              | float (>0) | Abfluss               | m³/s     | ✓       |
| `flap_gate_width`        | float (>0) | Breite der Klappe     | m        | ✓       |
| `flap_gate_height`       | float (>0) | Höhe der Klappe       | m        | ✓       |
| `flap_gate_angle`        | float      | Winkel zur Vertikalen | °        | ✓       |

#### Response Schema (Ausgabe)

| Feld             | Typ          | Beschreibung                              | Einheit  |
| ---------------- | ------------ | ----------------------------------------- | -------- |
| **Geometrie**    |
| `P_neu`          | float        | Effektive Wehrhöhe (nach Winkelkorrektur) | m        |
| **Hydraulik**    |
| `mu`             | float        | Abflussbeiwert                            | -        |
| `mu_ratio`       | float        | Verhältnis der Abflussbeiwerte            | -        |
| `hu`             | float        | Oberwasserstand über Wehrkrone            | m        |
| `yu`             | float        | Oberwasserstand (absolut)                 | m ü. NHN |
| `hd`             | float        | Unterwasserstand über Wehrkrone           | m        |
| `v`              | float        | Geschwindigkeit                           | m/s      |
| `vd`             | float        | Unterwasser-Geschwindigkeit               | m/s      |
| `beschleunigung` | float        | Beschleunigung entlang der Klappe         | m/(s·m)  |
| `h_gr`           | float        | Kritische Wassertiefe                     | m        |
| `v_gr`           | float        | Kritische Geschwindigkeit                 | m/s      |
| `warnings`       | List[string] | Warnungen (falls vorhanden)               | -        |

#### Beispiel Request

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

### 4. Betriebsmodell simulieren

**POST** `/operational-model`

Simuliert das Betriebsverhalten eines Labyrinth-Wehrs (optional mit Klappenwehr) über eine gesamte Abflusskurve.

#### Request Schema (Eingabe)

**Labyrinth-Parameter:**

- `bottom_level`, `downstream_water_level`, `discharge` (wie oben)
- `labyrinth_width`, `labyrinth_height`, `labyrinth_length`, `labyrinth_key_angle`

**Abfluss- und Wasserstandskurven:**

- `discharge_vector`: Liste von Abflusswerten [m³/s]
- `downstream_water_level_vector`: Liste von Unterwasserständen [m ü. NHN]
- `upstream_water_level_vector`: Liste von Ist-Oberwasserständen [m ü. NHN]

**Interpolation:**

- `interpolation_method`: "exponential", "linear", "quadratic", "cubic" (Default: "exponential")

**Optionale Klappenwehr-Parameter:**

- `flap_gate_bottom_level`, `flap_gate_downstream_water_level`, `flap_gate_discharge`
- `flap_gate_width`, `flap_gate_height`, `flap_gate_angle`

**Bemessungsparameter (bei Klappenwehr erforderlich):**

- `design_upstream_water_level`: Stauziel [m ü. NHN]
- `max_flap_gate_angle`: Maximaler Klappenwinkel [°]
- `fish_body_height`: Fischkörperhöhe für Bypass-Bemessung [m]

#### Response Schema (Ausgabe)

| Feld      | Typ    | Beschreibung  |
| --------- | ------ | ------------- |
| `message` | string | Statusmeldung |
| `status`  | string | Status        |

_Hinweis: Vollständige Implementierung folgt._

#### Beispiel Request

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

## Wichtige Hinweise

- **Einheiten:** Alle Längen in Metern [m], Abflüsse in m³/s, Winkel in Grad [°]
- **Wasserstände:** Absolute Werte in m ü. NHN (Meter über Normalhöhennull)
- **Optionale Parameter:** Werden nicht angegeben, werden Standardwerte verwendet
- **Validierung:** Die API validiert automatisch Eingabewerte (z.B. Abfluss > 0)
- **Warnungen:** Bei ungültigen Bereichsgrenzen werden Warnungen in `warnings` zurückgegeben

---

## Fehlerbehandlung

Die API gibt standardmäßige HTTP-Statuscodes zurück:

- **`200 OK`**: Erfolgreiche Berechnung.
- **`422 Unprocessable Entity`**: Eingabefehler.
  - Entweder Pydantic-Validierung (z.B. fehlende Pflichtfelder, falsche Typen), dann enthält `detail` die üblichen FastAPI/Pydantic-Felddetails.
  - Oder fachliche Validierung aus dem ENGINEER-Kern (`EngineerInputError`), z.B.:
    - negative oder nicht plausible hydraulische Größen (Abfluss, Höhen, Winkel),
    - Unterwasser ≤ Sohle (UW - Sohle ≤ 0),
    - bei `/operational`: leere Vektoren oder Vektoren mit unterschiedlicher Länge.
  - In diesen Fällen liefern die Endpunkte ein `detail`-Objekt der Form:
    - Labyrinth / Flap: `{"message": "...", "errors": ["Fehler 1", "Fehler 2", ...]}`
    - Operational: `{"message": "Operational model input is invalid.", "errors": [...]}`.
- **`500 Internal Server Error`**: Unerwarteter Serverfehler.
  - Für `/operational` wird ein strukturiertes JSON zurückgegeben:
    `{"message": "Operational model failed due to an internal error.", "error_type": "...", "error": "..."}`.

Bei Validierungsfehlern enthält die Antwort Details zu den fehlerhaften Feldern bzw. eine Liste fachlicher Fehlermeldungen.
