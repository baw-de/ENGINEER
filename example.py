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

from engineer import labyrinth, betriebsmodell, klappe, optimale_Labyrinth, UW_interpolation,kopplung,tosbecken,plot_check_FAA_FAbA, write_flap_excel, write_lab_excel
import matplotlib.pyplot as plt
import numpy as np
import os, shutil
import pandas as pd

plt.close('all')

#%% Labyrinth-Wehr
# Initialisierung
# Initialise the labyrinth-weir object

lab = labyrinth(sohleHoehe=0.1,     #bottom height [m]  
            UW=1.09,                #downstream Water level [m]
            Q=10,                   #discharge [m3/s]
            labyrinthBreite=15,     #labyrinth weir width [m]
            labyrinthHoehe=2.2,     #labyrinth weir height [m]
            labyrinthLaenge=8,      #labyrinth weir length in flow direction [m]
            keyWinkel=8,            #key angle [degree]
            D=0.5)                  #front wall width [m]

# Adjust parameters
# After adjustment of parameters, the hydraulics ans geometry mus be recalculated
# lab.D = 0.5
# lab.geometrie()
# lab.update()

# Plot the labyerinth geometyr
# lab.plot_geometry()


#%% flap gate
# (Fischbauch)klappe
# Usage like the labyrinth
kla  = klappe(sohleHoehe=0.1,       #bottom height [m]
              UW=1.09,              #downstream water level [m]
              Q=10,                 #discharge [m3/s]
              klappeBreite=1.4,     #flap width [m]
              klappeHoehe=2.35,     #flap height [m]
              klappeWinkel=74)      #flap angle [degree]



#%% Optimize the geometry of the labyrinth weir to the maximum hydraulic capacity
# Boundary conditions: 
# - the available space for the labyrinth weir
# - the design discharge
# - the crest height of the labyrinth (= minimum upstream water level)

sohlhoehe = 0.1         #bottom height [m]
breiteBaufeld = 10      #available width for the labyrinth weir [m]
laengeBaufeld = 8       #available length in flow direction for the labyrinth weir [m]
Q_HQ = 20               #design discharge [m3/s]
UW_HQ = 1.8             #downstream water level at design discharge [m]
OK_Labyrinth = 2.2      #crest height of labyrinth weir [m]    

# Optimization: the return value is an labyrinth-object
bestLab = optimale_Labyrinth(labyrinth, sohlhoehe, UW_HQ, Q_HQ, breiteBaufeld, OK_Labyrinth-sohlhoehe+0, laengeBaufeld,path='',show_plot=False)

# Postprozess
bestLab.plot_geometry()     #plot the optimized geometry
bestLab.verbose = 1         #print output
bestLab.print_results()     #print result parameters




#%% Operational model
# Here, the effect of the labyrinth weir system (labyrinth+flap) is simulated along the entire discharge curve.
# In doing so, the target water level is maintained for as long as possible by controlling the flap.
Stauziel = 2.2          #design water level [m]
Kalpha_max = 90         #maximum opening angle of the flap gate [degree]
H_fische = 0.4          #body height of the design fish [m]



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

results, results_events = betriebsmodell(Lab = bestLab,
                              Kla =  kla,
                              Abfluss = discharge,
                              Unterwasser = downstream_water_level,
                              Oberwasser = upstream_water_level_today,
                              Stauziel = Stauziel,
                              KlappeWinkel_max = Kalpha_max,
                              H_fische= H_fische,
                              interpolation='exponential',
                              show_plot=True,
                              save_plot=True)





        
    
write_lab_excel(lab)
write_flap_excel(kla)


