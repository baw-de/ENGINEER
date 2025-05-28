# -*- coding: utf-8 -*-
"""
Created on Thu Sep 15 13:32:37 2022

@author: fbelzner

ENGINEER

Copyright (C) 2024 Bundesanstalt für Wasserbau, Germany

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

#%% Module laden

import matplotlib.pyplot as plt
import numpy as np

from engineer import labyrinth, operational_model, klappe, optimale_Labyrinth, write_flap_excel, write_lab_excel

plt.close('all')

#%% Labyrinth-Wehr
# Initialisierung
# Initialise the labyrinth-weir object

labyrinth_weir = labyrinth(bottom_level=0.1,  #bottom height [m]
                           downstream_water_level=1.09,  #downstream Water level [m]
                           discharge=10,  #discharge [m3/s]
                           labyrinth_width=15,  #labyrinth weir width [m]
                           labyrinth_height=2.2,  #labyrinth weir height [m]
                           labyrinth_length=8,  #labyrinth weir length in flow direction [m]
                           labyrinth_key_angle=8,  #key angle [degree]
                           D=0.5)                  #front wall width [m]

# Adjust parameters
# After adjustment of parameters, the hydraulics and geometry mus be recalculated
# lab.D = 0.5
# lab.geometrie()
# lab.update()

# Plot the labyrinth geometry
# lab.plot_geometry()


#%% flap gate
# (Fischbauch)klappe
# Usage like the labyrinth
flap_gate  = klappe(bottom_level=0.1,  #bottom height [m]
                    downstream_water_level=1.09,  #downstream water level [m]
                    discharge=10,  #discharge [m3/s]
                    flap_gate_width=1.4,  #flap width [m]
                    flap_gate_height=2.35,  #flap height [m]
                    flap_gate_angle=74)      #flap angle [degree]



#%% Optimize the geometry of the labyrinth weir to the maximum hydraulic capacity
# Boundary conditions: 
# - the available space for the labyrinth weir
# - the design discharge
# - the crest height of the labyrinth (= minimum upstream water level)

bottom_level = 0.1         #bottom height [m]
labyrinth_width = 10      #available width for the labyrinth weir [m]
labyrinth_length = 8       #available length in flow direction for the labyrinth weir [m]
design_discharge = 20               #design discharge [m3/s]
design_downstream_water_level = 1.8             #downstream water level at design discharge [m]
labyrinth_crest_height = 2.2      #crest height of labyrinth weir [m]

# Optimization: the return value is a labyrinth-object
optimized_labyrinth = optimale_Labyrinth(labyrinth, bottom_level, design_downstream_water_level, design_discharge, labyrinth_width, labyrinth_crest_height - bottom_level + 0, labyrinth_length, path='', show_plot=False)

# Postprozess
optimized_labyrinth.plot_geometry()     #plot the optimized geometry
optimized_labyrinth.verbose = 1         #print output
optimized_labyrinth.print_results()     #print result parameters

#%% Operational model
# Here, the effect of the labyrinth weir system (labyrinth+flap) is simulated along the entire discharge curve.
# In doing so, the target water level is maintained for as long as possible by controlling the flap.
design_upstream_water_level = 2.2          #design water level [m]
max_flap_gate_angle = 90         #maximum opening angle of the flap gate [degree]
fish_body_height = 0.4          #body height of the design fish [m]

# Hydrology
# Is required to calculate the hydraulic effect along the entire discharge curve
discharge = np.array([
        2.09,
        2.79,
        6.01,
        11.90,
        13.90,
        16.30,
        16.50,
        18.60,
        20.50,
        22.90,
        24.50])

downstream_water_level = np.array([
            1.07,
            1.15,
            1.19,
            1.25,
            1.38,
            1.39,
            1.74,
            1.74,
            1.94,
            2.67,
            2.67])

# This is the current water level. This is used to compare the hydraulic effect of the labyrinth weir system with the current situation.
upstream_water_level_today = np.array([
            2.03,
            2.15,
            2.16,
            2.19,
            2.22,
            2.21,
            2.33,
            2.33,
            2.47,
            2.47,
            2.47])


#UW_interpolation(Abfluss,Unterwasser,interpolation='all',show_plot=True, save_plot=True)

results, results_events = operational_model(labyrinth_object = optimized_labyrinth,
                                            flap_gate_opject = flap_gate,
                                            discharge_vector= discharge,
                                            downstream_water_level_vector = downstream_water_level,
                                            upstream_water_level_vector = upstream_water_level_today,
                                            design_upstream_water_level = design_upstream_water_level,
                                            max_flap_gate_angle= max_flap_gate_angle,
                                            fish_body_height= fish_body_height,
                                            interpolation_method='exponential',
                                            show_plot=False,
                                            save_plot=False)







write_lab_excel(labyrinth_weir)
write_flap_excel(flap_gate)


