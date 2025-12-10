#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  9 14:36:15 2025

@author: belzner
"""

import requests



## Geometrie-Optimierung
url = "http://127.0.0.1:8000/labyrinth/optimize"

data = {
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

response = requests.post(url, json=data)
result = response.json()

print("Status:", response.status_code)
print("Antwort:", response.text)


## Labyrinth-Hydraulik (nutzt die Ergegnisse der Optimierung)
url = "http://127.0.0.1:8000/labyrinth/compute"

data = {
  "bottom_level": 0.1,
  "downstream_water_level": 1.09,
  "discharge": 10,
  "labyrinth_width": 15,
  "labyrinth_height": 2.2,
  "labyrinth_length": result['l_best'],
  "labyrinth_key_angle": result['Angle_best'],
  "D": 0.5,
  "t": 0.3
}

response = requests.post(url, json=data)
result = response.json()

print("Status:", response.status_code)
print("Antwort:", response.text)


## Klappe
url = "http://127.0.0.1:8000/flap/compute"

data = {
  "bottom_level": 0.1,
  "downstream_water_level": 1.09,
  "discharge": 10,
  "flap_gate_width": 1.4,
  "flap_gate_height": 2.35,
  "flap_gate_angle": 74
}

response = requests.post(url, json=data)
result = response.json()

print("Status:", response.status_code)
print("Antwort:", response.text)



## Operational Model (inkl. Kopplung)
url = "http://127.0.0.1:8000/operational"

data = {
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

response = requests.post(url, json=data)
result = response.json()

print("Status:", response.status_code)
print("Antwort:", response.text)