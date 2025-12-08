# -*- coding: utf-8 -*-
"""
Created on Wed Aug  3 14:05:07 2022

@author: Somasekhar-version94

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

import math
import os
import re

import matplotlib
# Automatically use non-GUI backend in server mode
if os.environ.get("SERVER_MODE") == "1":
    matplotlib.use("Agg")  # use non-GUI backend for server / headless environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Arc
from scipy.interpolate import interp1d
from scipy.optimize import fsolve, curve_fit, minimize, minimize_scalar


class EngineerInputError(Exception):
    """Grouping of all input errors."""

    def __init__(self, messages):
        if isinstance(messages, str):
            self.messages = [messages]
        else:
            self.messages = list(messages)
        message = "; ".join(self.messages) if self.messages else "Invalid input parameters."
        super().__init__(message)

'''plots format style'''''''''''''''''''''

plt.rcParams['text.usetex'] = False
plt.rcParams['font.family'] = 'serif'
# plt.rcParams['font.serif'] = ['Cambria']
plt.rcParams['font.size'] = 11
plt.rcParams['axes.grid'] = True
plt.rcParams['axes.grid.axis'] = 'both'
plt.rcParams['axes.grid.which'] = 'both'
plt.rcParams['grid.linestyle'] = 'dashed'
plt.rcParams['grid.linewidth'] = 0.5
plt.rcParams['grid.color'] = 'grey'
plt.rcParams['grid.alpha'] = 0.8
plt.rcParams['figure.figsize'] = (6.5, 7.5)  # size in inches
plt.rcParams['lines.linewidth'] = 1
plt.rcParams['lines.markersize'] = 4

plt.rcParams['figure.subplot.left'] = 0.125
plt.rcParams['figure.subplot.right'] = 0.9
plt.rcParams['figure.subplot.bottom'] = 0.09
plt.rcParams['figure.subplot.top'] = 0.975

''''''''''''''''''''''''''''''''''''''


class Labyrinth():  # this is only one geometry

    def __init__(self, bottom_level=None, downstream_water_level=None, discharge=None, labyrinth_width=None,
                 labyrinth_height=None, labyrinth_length=None, labyrinth_key_angle=None, path='', show_errors=True,
                 show_geometry=False, show_results=False, D=0.3, t=0.3, skip_zero_check=False):  # instance attribute
        self.Sh = bottom_level  # Sohlhöhe [m ü. NHN]
        self.UW = downstream_water_level  # Unterwasserstand [m ü. NHN]
        self.Q = discharge  # Abfluss [m3/sec]
        self.W = labyrinth_width  # Labyrinth_Breite [m]
        self.B = labyrinth_length  # Labyrinth_Laenge [m]    #tino
        self.P = labyrinth_height
        self.alpha = labyrinth_key_angle
        self.gravity = 9.81  # g = Erdbeschleunigung [m2/sec]
        self.D = D  # D  = Dicke der Stirnwand
        self.t = t
        self.show_errors = show_errors
        self.verbose = show_results
        self.show_geometry = show_geometry
        self.path = path
        self.skip_zero_check = skip_zero_check

        if all(var is not None for var in (self.Sh, self.Q, self.UW, self.W, self.B, self.P, self.alpha)):
            self.check_and_exit_on_input_errors()
            self.geometrie()
            self.__angle_result()  # private Methode
            self.cal_Q()
            self.cal_hd()
            self.cal_v()
            self.cal_hu()
            self.cal_yu()
            self.check_for_error()

    def update(self):
        self.check_and_exit_on_input_errors()
        self.geometrie()
        self.cal_Q()
        self.cal_hd()
        self.cal_v()
        self.cal_hu()
        self.check_for_error()
        # self.print_results()
        self.cal_yu()

    def check_and_exit_on_input_errors(self):
        def input_plausibilty(eingabe_name, eingabe_wert, max_value=None, min_value=None):
            fehler = []  # Store error messages

            if not self.skip_zero_check and eingabe_wert <= 0:
                if re.search(r'(Unterwasser|SohleHoehe)', eingabe_name):
                    fehler.append(f"Achtung: {eingabe_name} Wert ist negative.")
                else:
                    fehler.append(f"{eingabe_name} Wert ist nicht plausibel (sollte größer als 0 sein).")

            if max_value is not None and eingabe_wert > max_value:
                fehler.append(f"{eingabe_name} Wert sollte {max_value} nicht überschreiten.")

            if min_value is not None and eingabe_wert < min_value:
                fehler.append(f"{eingabe_name} Wert sollte nicht kleiner sein als {min_value}.")

            return fehler  # Return list of fehler

        fehler = []  # Initialize the fehler list

        fehler += input_plausibilty("SohleHoehe", self.Sh)
        fehler += input_plausibilty("Unterwasser", self.UW)
        fehler += input_plausibilty("Abfluss", self.Q)
        fehler += input_plausibilty("Labyrinth Breite", self.W)
        fehler += input_plausibilty("Labyrinth Laenge", self.B)
        fehler += input_plausibilty("Labyrinth Hoehe", self.P)
        fehler += input_plausibilty("Keywinkel", self.alpha)
        fehler += input_plausibilty("D", self.D)
        fehler += input_plausibilty("t", self.t)

        # additional combined plausibility checks that depend on multiple parameters
        # ensure that downstream water level is above the bottom level to avoid zero water depth
        if not self.skip_zero_check and self.UW - self.Sh <= 0:
            fehler.append("Unterwasser muss über der Sohle liegen (UW - SohleHoehe > 0).")

        if all(fehler_message.startswith("Achtung:") for fehler_message in fehler):
            # Only warnings -> optionally print to console, but allow computation to continue
            for i, fehler_message in enumerate(fehler, start=1):
                print(f"[Labyrinth] {i}. {fehler_message}")
            fehler = None
        else:
            # Hard input errors -> raise exception without additional print (avoid duplicate output)
            raise EngineerInputError(fehler)

    # Berechnung der Wehrgeometrie
    def geometrie(self):

        self.w = 2 * (self.D + self.B * (math.tan(math.radians(self.alpha))))  # w = Breite der einzelnen Keys
        self.l = self.B / math.cos(math.radians(self.alpha))  # Länge der einzelnen schrägen Seitenwände
        self.N = math.floor(self.W / self.w)  # Anazahl der Keys
        self.S = self.W - self.N * self.w  # S = Seitenlänge
        self.L = self.S + 2 * self.N * (self.D + self.l)  # Länge des Labyrinthwehrs

        return self.w, self.l, self.N, self.S, self.L

    # Abrufen von Konstanten aus Alpha_result, Private method
    def __angle_result(self):

        Angle_kons = np.array([[6, 0.009447, -4.039, 0.3955, 0.187],
                               [8, 0.017090, -3.497, 0.4048, 0.2286],
                               [10, 0.029900, -2.978, 0.4107, 0.2520],
                               [12, 0.030390, -3.102, 0.4393, 0.2912],
                               [15, 0.031600, -3.270, 0.4849, 0.3349],
                               [20, 0.033610, -3.500, 0.5536, 0.3923],
                               [35, 0.018550, -4.904, 0.6697, 0.5062]])

        # Berechnung der Winkelkonstanten

        self.a = np.interp(self.alpha, Angle_kons[:, 0], Angle_kons[:, 1])

        self.b = np.interp(self.alpha, Angle_kons[:, 0], Angle_kons[:, 2])

        self.c = np.interp(self.alpha, Angle_kons[:, 0], Angle_kons[:, 3])

        self.d = np.interp(self.alpha, Angle_kons[:, 0], Angle_kons[:, 4])

        # Berechnung von Abfluss

    def cal_Q(self):

        self.__angle_result()
        Cd_alt = 0.1

        Cd_neu = 1

        n = 0

        while n >= 0:

            n = n + 1

            Hu_alt = pow((1.5 * (self.Q / (Cd_alt * self.L * pow((2 * self.gravity), 0.5)))), (2 / 3))

            Cd_neu = self.a * pow((Hu_alt / self.P), (self.b * (pow((Hu_alt / self.P), self.c)))) + self.d

            Q_neu = (2 / 3) * Cd_neu * self.L * pow((2 * self.gravity), 0.5) * pow(Hu_alt, 1.5)
            # print('Q_neu = ' + str(Q_neu)) #DEBUG

            # if Cd_neu - Cd_alt <= 0.0001:
            #     print('Number  of iterations for Cd: ' + str(n))
            #     break

            if abs(Q_neu - self.Q) < 0.01:
                break

            Cd_alt = Cd_neu

        self.Cd = Cd_neu
        self.Hu = Hu_alt

        return self.Cd, self.Hu

    # Rückstaueinfluss
    def cal_hd(self):

        self.hd = (self.UW - self.Sh) - self.P
        self.vd = self.Q / (self.W * (self.hd + self.P))
        self.Hd = self.hd + ((self.vd * self.vd) / (2 * self.gravity))
        self.rs = "Kein Rückstaueinfluss!"

        if self.hd > 0:
            self.rs = "Rückstaueinfluss!"
            self.cal_ruckstauH()

        # Berechnung der Geschwindigkeit
        self.v = self.cal_v()

        return self.hd, self.v

    # Berechnung des Oberwasserspiegels bei Rückstaueinflusses
    def cal_ruckstauH(self):

        if self.Hu != 0:
            R = self.Hd / self.Hu
        else:
            R = np.nan

        if 0 <= R <= 1.53:
            H = self.Hu * ((0.0332 * pow(R, 4)) + (0.2008 * pow(R, 2) + 1))

        elif 1.53 < R <= 3.5:
            H = self.Hu * ((0.9379 * R) + 0.2174)

        else:
            H = self.Hd

        self.Hu = H

    # Berechnung der Geschwindigkeit
    def cal_v(self):

        v_alt = 0.1
        m = 0

        while m >= 0:
            m = m + 1
            h = self.Hu - ((v_alt * v_alt) / (2 * self.gravity))
            v_neu = self.Q / (self.W * (h + self.P))

            if v_alt - v_neu <= 0.000001:
                break
            v_alt = v_neu

        self.v = v_neu

        return self.v

    def cal_hu(self):

        self.hu = self.Hu - pow(self.v, 2) / (2 * self.gravity)

    def cal_yu(self):

        self.yu = self.Sh + self.P + self.hu

    # Druckergebnisse
    def print_results(self):
        if self.verbose:
            self.show_errors = True
            self.check_for_error()
            print('Key Laenge = %2.2f [m]' % self.B, '\n'
                                                     'Key Frontwand =', self.D, '[m]\n'
                                                                                'Key Winkel =', self.alpha, '[°]\n'
                                                                                                            'Key Wandstaerke =',
                  self.t, '[m]\n'
                          'Key Hoehe = %2.2f' % self.P, '[m]\n'
                                                        'Key Anzahl =', self.N, '\n'
                                                                                'Key Weite = %2.2f [m]' % self.w, '\n'
                                                                                                                  'Keys Weite = %2.2f [m]' % (
                              self.N * self.w), '\n'
                                                'Seite Weite[S] = %2.2f [m]' % self.S, '\n'
                                                                                       'Wehr Weite = %2.2f [m]' % self.W,
                  '\n'
                  'L/W = %2.2f [m]' % (self.L / self.W), '\n'
                                                         'Hu = %2.2f [m]' % self.Hu, '\n',
                  'hu = %2.2f [m]' % self.hu, '\n',
                  self.rs, '\n',
                  self.ce if self.ce != 0 else '')

    # Grenzen der Variablen
    def check_for_error(self):
        if self.show_errors:
            self.ce = 0
            if not 0.05 < self.Hu / self.P < 1:
                self.ce = "Cd-Wert des Labywrinth-Wehrs könnte fehlerhaft sein, da H/P außerhalb des Bereichs liegt"
            if not self.w / self.P < 4:
                self.ce = "Cd-Wert des Labywrinth-Wehrs könnte fehlerhaft sein, da w/P außerhalb des Bereichs liegt"
            if not self.L / self.W < 7.6:
                self.ce = "Cd-Wert des Labywrinth-Wehrs könnte fehlerhaft sein, da L/W außerhalb des Bereichs liegt"

    # Plotten Labyrinth-Wehr
    def plot_geometry(self):

        # plt.close()

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)

        if self.N > 0:

            a = self.D / 2  # Konstanten
            b = self.B * (math.tan(math.radians(self.alpha)))  # Konstanten

            Labyrinth_wehr = np.zeros((self.N * 6 + 1, 2))

            for i in np.arange(0, self.N * 6, 6):
                # Zuweisung der x-Koordinate
                Labyrinth_wehr[i + 1, 0] = Labyrinth_wehr[i, 0] + a
                Labyrinth_wehr[i + 2, 0] = Labyrinth_wehr[i + 1, 0] + b
                Labyrinth_wehr[i + 3, 0] = Labyrinth_wehr[i + 2, 0] + self.D
                Labyrinth_wehr[i + 4, 0] = Labyrinth_wehr[i + 3, 0] + b
                Labyrinth_wehr[i + 5, 0] = Labyrinth_wehr[i + 4, 0] + a
                Labyrinth_wehr[i + 6, 0] = Labyrinth_wehr[i + 4, 0] + a

                # Zuweisung der y -Koordinate
                Labyrinth_wehr[i + 2, 1] = self.B
                Labyrinth_wehr[i + 3, 1] = self.B

            # Labyrinth_wehr  #Ohne self.S

            Labyrinth_wehr[:, 0] += self.S / 2  # Verschiebung aller Koordinaten um self.S/2

            Labyrinth_wehr = np.insert(Labyrinth_wehr, 0, np.array((0, 0)), 0)  # Hinzufügung von Origin koordinatoren

            Labyrinth_wehr = np.insert(Labyrinth_wehr, len(Labyrinth_wehr),
                                       np.array((Labyrinth_wehr[-1, 0] + self.S / 2, 0)),
                                       0)  # Hinzufügen der letzten Koordinate

            # Plotting

            ax.plot(Labyrinth_wehr[:, 0], Labyrinth_wehr[:, 1])
            ax.set_ylim(-2, self.B + 2)
            ax.set_xlim(-2, self.W + 2)

            # Plot Angle
            # a = Arc((Labyrinth_wehr[1,0],Labyrinth_wehr[1,1]),1,1,0,0,45,color='red',lw=1)
            a = Arc((Labyrinth_wehr[1, 0], Labyrinth_wehr[1, 1]), 1, 1, angle=0, theta1=0, theta2=45, color='red', lw=1)
            ax.add_patch(a)

            # Annotation text
            ax.text(0.5 * (Labyrinth_wehr[3, 0] + Labyrinth_wehr[4, 0]), self.B + 0.2, 'D', size=14)
            ax.text(0.5 * Labyrinth_wehr[-1, 0], -0.1, 'W', size=14)
            ax.text(0, 0.5 * self.B, 'B', size=14)
            ax.text(Labyrinth_wehr[1, 0] + 0.5, Labyrinth_wehr[1, 1] + 0.2, r"$\alpha$", size=14)

            # Annotation arrows
            ax.annotate('', (Labyrinth_wehr[4, 0] + 0.1, self.B + 0.1), (Labyrinth_wehr[3, 0] - 0.1, self.B + 0.1),
                        arrowprops=dict(arrowstyle='<->', color='black'))
            ax.annotate('', (Labyrinth_wehr[-1, 0], -0.25), (Labyrinth_wehr[0, 0], -0.25),
                        arrowprops=dict(arrowstyle='<->', color='black'))
            ax.annotate('', (0, self.B), (Labyrinth_wehr[0, 0], 0), arrowprops=dict(arrowstyle='<->', color='black'))

            plt.show()
            # plt.savefig('result-'+str(self.B)+' '+str(self.alpha)+'.jpg')
            # fig,ax = plt.subplots(ncols=2)

        else:
            print('Plotten des Labyrinths ist mit', self.N, 'keys nicht möglich')

        if self.path:
            plt.savefig(self.path + '\\Labyrinth-Wehr_plot.svg')
            plt.savefig(self.path + '\\Labyrinth-Wehr_plot.pdf')
        else:
            plt.savefig('Labyrinth-Wehr_plot.svg')
            plt.savefig('Labyrinth-Wehr_plot.pdf')


# Berechnung einer hydraulisch optimalen Geometrie aus den baulichen Randbedingungen
def optimize_labyrinth_geometry(labyrinth, sohleHoehe, UW, Q, labyrinthBreite, labyrinthHoehe, labyrinthLaengeMax, path,
                                show_results=False, show_plot=False):
    B_vector = np.arange(1, labyrinthLaengeMax + 0.1, 0.1)
    Angle_vector = np.arange(6, 36, 1)

    # Erstellen von leeren 2d-Arrays zum Speichern von Geometrieergebnissen

    w_result = np.empty([np.size(B_vector), np.size(Angle_vector)])
    l_result = np.empty([np.size(B_vector), np.size(Angle_vector)])
    N_result = np.empty([np.size(B_vector), np.size(Angle_vector)])
    S_result = np.empty([np.size(B_vector), np.size(Angle_vector)])
    L_result = np.empty([np.size(B_vector), np.size(Angle_vector)])
    Hu_result = np.empty([np.size(B_vector), np.size(Angle_vector)])
    Cd_result = np.empty([np.size(B_vector), np.size(Angle_vector)])
    hd_result = np.empty([np.size(B_vector), np.size(Angle_vector)])
    v_result = np.empty([np.size(B_vector), np.size(Angle_vector)])

    for i, B in enumerate(B_vector):

        for j, alpha in enumerate(Angle_vector):  # float werte --- Table

            Lab = labyrinth(sohleHoehe, UW, Q, labyrinthBreite, labyrinthHoehe, B, alpha)
            Lab.update()
            # Lab.plot_geometry()
            w_result[i, j] = Lab.w
            l_result[i, j] = Lab.l
            N_result[i, j] = Lab.N
            S_result[i, j] = Lab.S
            L_result[i, j] = Lab.L
            Cd_result[i, j] = Lab.Cd
            Hu_result[i, j] = Lab.Hu
            hd_result[i, j] = Lab.Cd
            v_result[i, j] = Lab.v

            # Speicherung des H_min-Wertes und seine Index

    Hu_min = np.amin(Hu_result)
    i, j = np.where(Hu_result == Hu_min)[0], np.where(Hu_result == Hu_min)[1]
    i = i[0]
    j = j[0]

    Cd_best = Cd_result[i, j]
    Hu_best = Hu_result[i, j]
    hd_best = hd_result[i, j]
    v_best = v_result[i, j]
    Angle_best = Angle_vector[j]
    B_best = B_vector[i]
    w_best = w_result[i, j]
    l_best = l_result[i, j]
    N_best = N_result[i, j]
    S_best = S_result[i, j]
    L_best = L_result[i, j]

    bestLab = labyrinth(sohleHoehe, UW, Q, labyrinthBreite, labyrinthHoehe, B_best, Angle_best, path)

    if show_results:
        print('Optimale Geometrie des Wehre ist:', '\n',
              'Labyrinth Laenge = %2.2f [m]' % B_best, '\n',
              'Key Frontwand =', Lab.D, '[m]', '\n',
              'Key Winkel =', Angle_best, '[°]', '\n',
              'Key Wandstaerke =', Lab.t, ' [m]', '\n',
              'Labyrinth Hoehe = %2.2f [m]' % Lab.P, '\n',
              'Keys Anzahl = %2.0f [m]' % N_best, '\n',
              'Key Breite = %2.2f [m]' % w_best, '\n',
              'Keys Breite = %2.2f [m]' % (N_best * w_best), '\n',
              'Seite Breite[S] = %2.2f [m]' % S_best, '\n',
              'Labyrinth Breite = %2.2f [m]' % labyrinthBreite, '\n',
              'L/W = %2.2f [m]' % (L_best / labyrinthBreite), '\n',
              'Hu_min = %2.2f [m]' % Hu_best, '\n',
              )

    if show_plot:
        plt.figure()
        alphai, Bi = np.meshgrid(Angle_vector, B_vector)
        plt.pcolormesh(alphai, Bi, Hu_result, cmap='rainbow')  # imshow,pcolor options
        plt.xlabel('alpha [°]')
        plt.ylabel('B [m]')
        plt.grid()
        plt.colorbar()
        plt.show()
        plt.title('Original')

    return bestLab


class FlapGate():

    def __init__(self, bottom_level=None, downstream_water_level=None, discharge=None, flap_gate_width=None, flap_gate_height=None, flap_gate_angle=None,
                 show_errors=0, skip_zero_check=False):  # instance attribute
        self.Sh = bottom_level  # Sohlhöhe [m ü. NHN]
        self.UW = downstream_water_level  # Unterwasserstand [m ü. NHN]
        self.Q = discharge  # Abfluss [m3/sec]
        self.KW = flap_gate_width  # Breite des Klappe [m]
        self.KP = flap_gate_height
        self.Kalpha = flap_gate_angle
        self.g = 9.81  # g = Erdbeschleunigung [m2/sec]
        self.show_errors = show_errors
        self.skip_zero_check = skip_zero_check

        if all(var is not None for var in (self.Sh, self.Q, self.UW, self.KW, self.KP, self.Kalpha)):
            self.check_and_exit_on_input_errors()
            self.abflussbeiwert()
            self.abminderung_faktor()
            self.cal_P_neu()
            self.cal_Q()

            self.cal_hd()
            self.cal_v()
            self.cal_yu()
            self.cal_vd()
            self.FAA_FAbA()
        # self.check_for_error()

    def update(self):
        self.check_and_exit_on_input_errors()
        self.abflussbeiwert()
        self.cal_P_neu()
        self.cal_Q()

        self.cal_hd()
        self.cal_v()
        self.cal_yu()
        self.cal_vd()
        self.check_for_error()
        self.FAA_FAbA()
        # self.print_results()

    def check_and_exit_on_input_errors(self):
        def input_plausibilty(eingabe_name, eingabe_wert, max_value=None, min_value=None):
            fehler = []  # Store error messages

            if not self.skip_zero_check and eingabe_wert <= 0:
                if re.search(r'(Unterwasser|SohleHoehe)', eingabe_name):
                    fehler.append(f"Achtung: {eingabe_name} Wert ist negative.")
                else:
                    fehler.append(f"{eingabe_name} Wert ist nicht plausibel (sollte größer als 0 sein).")

            if max_value is not None and eingabe_wert > max_value:
                fehler.append(f"{eingabe_name} Wert sollte {max_value} nicht überschreiten.")

            if min_value is not None and eingabe_wert < min_value:
                fehler.append(f"{eingabe_name} Wert sollte nicht kleiner sein als {min_value}.")

            return fehler  # Return list of fehler

        fehler = []  # Initialize the fehler list

        fehler += input_plausibilty("SohleHoehe", self.Sh)
        fehler += input_plausibilty("Unterwasser", self.UW)
        fehler += input_plausibilty("Abfluss", self.Q)
        fehler += input_plausibilty("Klappe Breite", self.KW)
        fehler += input_plausibilty("Klappe Hoehe", self.KP)
        fehler += input_plausibilty("Klappe Winkel", self.Kalpha)

        # additional combined plausibility checks that depend on multiple parameters
        # ensure that downstream water level is above the bottom level to avoid zero water depth
        if not self.skip_zero_check and self.UW - self.Sh <= 0:
            fehler.append("Unterwasser (FlapGate) must be above the bottom level (UW - SohleHoehe > 0).")

        if all(message.startswith("Achtung:") for message in fehler):
            # Only warnings -> optionally print to console, but allow computation to continue
            for i, fehler_message in enumerate(fehler, start=1):
                print(f"[FlapGate] {i}. {fehler_message}")
            fehler = None
        else:
            # Hard input errors -> raise exception without additional print
            raise EngineerInputError(fehler)

    def abflussbeiwert(self):

        self.mu_verhältnis = np.array([[-42.74, 0.9143],
                                       [-39.05, 0.92],
                                       [-35.07, 0.9271],
                                       [-31.1, 0.9343],
                                       [-27.21, 0.9434],
                                       [-23.15, 0.9496],
                                       [-19.17, 0.9571],
                                       [-15.2, 0.9659],
                                       [-11.22, 0.9743],
                                       [-7.24, 0.9831],
                                       [-3.274, 0.9926],
                                       [0.6412, 1.002],
                                       [2.418, 1.009],
                                       [5.761, 1.015],
                                       [9.555, 1.025],
                                       [13.5, 1.034],
                                       [16.96, 1.046],
                                       [20.76, 1.055],
                                       [24.37, 1.065],
                                       [27.98, 1.074],
                                       [31.78, 1.084],
                                       [35.75, 1.094],
                                       [39.73, 1.104],
                                       [43.82, 1.11],
                                       [47.68, 1.118],
                                       [51.65, 1.124],
                                       [55.63, 1.128],
                                       [59.6, 1.131],
                                       [63.58, 1.13],
                                       [67.55, 1.127],
                                       [71.35, 1.119],
                                       [74.42, 1.109],
                                       [76.72, 1.098],
                                       [80.02, 1.079],
                                       [81.29, 1.069],
                                       [82.37, 1.058],
                                       [83.27, 1.051],
                                       [84.18, 1.038],
                                       [84.9, 1.03],
                                       [85.8, 1.015]])

        self.mu_ratio = np.interp(self.Kalpha, self.mu_verhältnis[:, 0], self.mu_verhältnis[:, 1])

    def abminderung_faktor(self):

        self.Abminderung_fak = np.array([[0.0112, 0.9916],
                                         [0.0718, 0.9764],
                                         [0.1610, 0.9473],
                                         [0.2191, 0.9268],
                                         [0.2801, 0.9032],
                                         [0.3396, 0.8775],
                                         [0.3992, 0.8500],
                                         [0.4588, 0.8201],
                                         [0.5184, 0.7877],
                                         [0.5780, 0.7525],
                                         [0.6377, 0.7127],
                                         [0.6976, 0.6707],
                                         [0.7572, 0.6168],
                                         [0.8107, 0.5622],
                                         [0.9055, 0.4440],
                                         [0.9382, 0.4055],
                                         [1, 0.3]])

    def cal_P_neu(self):
        self.P_neu = self.KP * (math.cos(math.radians(abs(self.Kalpha))))

    def cal_Q(self):

        mu_alt = 0.1

        n = 0

        while n >= 0:

            hu_alt = pow(self.Q / (2.953 * mu_alt * self.KW),
                         2 / 3)  # Tech. Hydro mechanik 1 - Gleichung 9.2 - Zeite 403

            mu90_neu = 0.615 * (1 + (1 / (1000 * hu_alt + 1.6))) * (1 + (0.5 * pow(hu_alt / (hu_alt + self.P_neu),
                                                                                   2)))  # Tech. Hydro mechanik 1 - Gleichung 9.16 - Zeite 415

            # =============================================================================
            #            Diese Formel gilt für
            #             w >= 0.3 ,
            #
            #             h / w <= 1,
            #
            #             0.025 <= h <= 0.8
            # =============================================================================

            mu_neu = self.mu_ratio * mu90_neu

            Q_neu = 2.953 * mu_neu * self.KW * pow(hu_alt, 3 / 2)

            if abs(Q_neu - self.Q) < 0.01:
                break

            mu_alt = mu_neu

        self.mu = mu_neu

        self.hu = hu_alt  # In der Literatur wird sie als h bezeichnet

    # Wehr höhe = self.P *sin(90-alpha),sin(90-alpha) = cos(alpha)

    def cal_hd(self):
        self.hd = (self.UW - self.Sh) - self.P_neu  # In der Literatur wird sie als hu bezeichnet

        if self.hd > 0:
            # print(self.Q,self.UW,self.hd)
            self.cal_ruckstauH()

    def cal_ruckstauH(self):
        def f(h):
            # print (self.hd,h[0],self.hd/h[0])
            if h[0] < self.hd:
                h[0] = self.hd + 0.01
            return (pow((1 - pow((self.hd / h), 1.15)), 0.37) * 2.953
                    * 0.615 * (1 + (1 / (1000 * h + 1.6))) * (1 + (0.5 * pow(h / (h + self.P_neu), 2)))
                    * self.mu_ratio
                    * self.KW * pow(h, 1.5) - self.Q)

        # def f(h):
        #     return ((np.interp(self.hd/h0,self.Abminderung_fak[:,0],self.Abminderung_fak[:,1]))*2.953
        #             *0.615*(1+(1/(1000*h+1.6)))*(1+(0.5*pow(h/(h+self.P_neu),2)))
        #             *self.mu_ratio
        #             *self.KW*pow(h,1.5)-self.Q)

        h0 = self.hd + 0.1

        self.hu = fsolve(f, h0)[
            0]  # Der Rückgabetyp der Funktion fsolve ist array, hier wird array in float umgewandelt

    def cal_v(self):

        if self.hu == 0:
            self.v = np.nan

        else:
            self.v = self.Q / (self.KW * self.hu)

    def cal_yu(self):

        self.yu = self.Sh + self.P_neu + self.hu

    def cal_vd(self):

        self.vd = self.Q / (self.KW * (self.UW - self.Sh))

    def FAA_FAbA(self):

        self.h_gr = pow((pow(self.Q / self.KW, 2)) / self.g, 0.33)
        self.v_gr = pow((self.g * self.h_gr), 0.5)
        self.beschleunigung = (self.v_gr - self.v) / (self.KP * (math.sin(math.radians(abs(self.Kalpha)))))

    # Grenzen der Variablen
    def check_for_error(self):
        if self.show_errors:
            self.ce = "No errors"
            if not 0.025 <= self.hu <= 0.80:
                self.ce = "Cd kann nicht berechnet werden, da hu außerhalb des Bereichs liegt"
            if not self.hu / self.KP <= 1:
                self.ce = "Cd kann nicht berechnet werden, da hu/P außerhalb des Bereichs liegt"
            if not self.KP >= 0.3:
                self.ce = "Cd kann nicht berechnet werden, da P außerhalb des Bereichs liegt"

    def print_results(self):
        self.show_errors = True
        self.check_for_error()
        print('Hoehe =', self.KP, '[m]\n',
              'Breite =', self.KW, '[m]\n',
              'Winkel zur Vertikalen = %2.2f [°]' % self.Kalpha, '\n',
              'mu_ratio = %2.2f' % self.mu_ratio, '\n',
              'mu = %2.2f' % self.mu, '\n',
              'Oberwasserstand über OK = %2.2f [m]' % self.hu, '\n',
              'Oberwasserstand = %2.2f [m ü. NHN]' % self.yu, '\n',
              'Unterwasserstand über OK = %2.2f [m]' % self.hd, '\n',
              'Unterwasserstand =%2.2f [m ü. NHN]' % self.UW, '\n')


def kopplung(Q, UW, Lab, Kla):  # Funktion zur Optimierung der Entladung zwischen Labyrinth und Klappe

    def check_and_exit_on_input_errors():
        def input_plausibilty(eingabe_name, eingabe_wert, max_value=None, min_value=None):
            fehler = []  # Store error messages

            if eingabe_wert <= 0:
                if re.search(r'(Unterwasser|SohleHoehe)', eingabe_name):
                    fehler.append(f"Achtung: {eingabe_name} Wert ist negative.")
                else:
                    fehler.append(f"{eingabe_name} Wert ist nicht plausibel (sollte größer als 0 sein).")

            if max_value is not None and eingabe_wert > max_value:
                fehler.append(f"{eingabe_name} Wert sollte {max_value} nicht überschreiten.")

            if min_value is not None and eingabe_wert < min_value:
                fehler.append(f"{eingabe_name} Wert sollte nicht kleiner sein als {min_value}.")

            return fehler  # Return list of fehler

        fehler = []  # Initialize the fehler list

        fehler += input_plausibilty("Unterwasser", UW)
        fehler += input_plausibilty("Abfluss", Q)

    fehler = check_and_exit_on_input_errors()
    if fehler:
        print(f"[kopplung] Eingabefehler: {fehler}")
        return fehler

    # check_and_exit_on_input_errors()

    Lab.UW = UW
    Kla.UW = UW

    def teilung(Q, Lab, Kla):

        def Objective_fn(i):
            a = i[0]
            Lab.Q = a * Q
            Kla.Q = (1 - a) * Q
            Lab.update()
            Kla.update()
            return abs(Lab.yu - Kla.yu)

        # bounds
        bounds_a = (0.0025, 0.99)
        bounds = [bounds_a]

        # initial values
        i0 = [0.0025]

        # constraints
        # con = {'type':'eq','fun':constraint}

        # minmize function
        result = minimize(Objective_fn, i0, bounds=bounds)

        return result.x[0], (1 - result.x[0])

    # =============================================================================
    #     def teilung(Q,Lab,Kla):
    #
    #         a = 0.0025
    #
    #         while  a >=0:
    #             Lab.Q = a* Q
    #             Kla.Q = (1-a)* Q
    #             Lab.update()
    #             Kla.update()
    #
    #             #print(Q,Lab.Q,Kla.Q,Lab.yu,Kla.yu,a,round(abs(Kla.yu - Lab.yu),2))
    #             if abs(Kla.yu - Lab.yu) <= 0.05:
    #                 break
    #
    #             a = round(a + 0.0025,3)
    #
    #         return a,(1-a)
    # =============================================================================

    if Lab.P > Kla.P_neu:
        # print('Lab.P=',Lab.P,'Kla.P_neu=',Kla.P_neu)
        Lab.Q = 0.00
        Lab.skip_zero_check = True
        Kla.Q = Q
        Lab.update()
        Kla.update()
        Lab.yu = Kla.yu

        if Kla.yu > (Lab.Sh + Lab.P):
            # print(Kla.hu,Kla.yu,Lab.Sh+Lab.P,Kla.Kalpha)
            a, b = teilung(Q, Lab, Kla)
            # Lab.Q = a * Q
            # Kla.Q = b * Q
            # Lab.update()
            # Kla.update()

        return Lab.Q, Kla.Q, Lab.yu, Kla.yu

    elif Kla.P_neu > Lab.P:
        # print('Lab.P=',Lab.P,'Kla.P_neu=',Kla.P_neu)
        Kla.Q = 0.00
        Kla.skip_zero_check = True
        Lab.Q = Q
        Kla.update()
        Lab.update()
        if Lab.yu > (Kla.Sh + Kla.P_neu):
            a, b = teilung(Q, Lab, Kla)
            # Lab.Q = a * Q
            # Kla.Q = b * Q
            # Lab.update()
            # Kla.update()

        return Lab.Q, Kla.Q, Lab.yu, Kla.yu

    else:
        # print('Lab.P=',Lab.P,'Kla.P_neu=',Kla.P_neu)
        a, b = teilung(Q, Lab, Kla)
        # Lab.Q = a * Q
        # Kla.Q = b * Q
        # Lab.update()
        # Kla.update()

        return Lab.Q, Kla.Q, Lab.yu, Kla.yu


def UW_interpolation(Abfluss, Unterwasser, interpolation, path='', show_plot=False, save_plot=False):
    def check_and_exit_on_input_errors():
        def input_plausibilty(eingabe_name, eingabe_wert, max_value=None, min_value=None):
            fehler = []  # Store error messages

            if eingabe_wert <= 0:
                if re.search(r'(Unterwasser)', eingabe_name):
                    fehler.append(f"Achtung: {eingabe_name} Wert ist negative.")
                else:
                    fehler.append(f"{eingabe_name} Wert ist nicht plausibel (sollte größer als 0 sein).")

            if max_value is not None and eingabe_wert > max_value:
                fehler.append(f"{eingabe_name} Wert sollte {max_value} nicht überschreiten.")

            if min_value is not None and eingabe_wert < min_value:
                fehler.append(f"{eingabe_name} Wert sollte nicht kleiner sein als {min_value}.")

            return fehler  # Return list of fehler

        fehler = []  # Initialize the fehler list

        valid_interpolations = ["exponential", "linear", "quadratic", "cubic", "all"]
        if interpolation not in valid_interpolations:
            fehler.append("Interpolationsmethode ist ungültig.")

        # Check Abfluss values
        for i, abfluss_wert in enumerate(Abfluss):
            fehler_abfluss = input_plausibilty("Abfluss " + str(Abfluss[i]), abfluss_wert)
            fehler.extend(fehler_abfluss)

        for i, unterwasser_wert in enumerate(Unterwasser):
            fehler_unterwasser = input_plausibilty("Unterwasser " + str(Unterwasser[i]), unterwasser_wert)
            fehler.extend(fehler_unterwasser)

        return fehler

    fehler = check_and_exit_on_input_errors()
    if all(message.startswith("Achtung:") for message in fehler):
        # Only warnings -> optionally print to console
        for i, fehler_message in enumerate(fehler, start=1):
            print(f"[UW_interpolation] {i}. {fehler_message}")
        fehler = None
    else:
        # Harte Eingabefehler -> Exception, kein zusätzlicher Print
        raise EngineerInputError(fehler)

    def perform_interpolation(interpolation, Abfluss, Unterwasser, Q_con):
        if interpolation == 'exponential':
            def model_f(x, a, b, c):
                return a * (np.exp(b * x)) + c

            popt, pcov = curve_fit(model_f, Abfluss, Unterwasser, p0=[0., 0.1, 0.1], maxfev=2000)
            a_opt, b_opt, c_opt = popt

            UW1 = a_opt * (np.exp(b_opt * Abfluss)) + c_opt
            UW2 = a_opt * (np.exp(b_opt * Q_con)) + c_opt

            # Calculate Mean Squared Error
            MSE = np.mean((Unterwasser - UW1) ** 2)
            # Calculate R-squared
            SSR = np.sum((Unterwasser - UW1) ** 2)
            SST = np.sum((Unterwasser - np.mean(UW1)) ** 2)
            R_squared = 1 - (SSR / SST)

        elif interpolation == 'linear':
            coeffs = np.polyfit(Abfluss, Unterwasser, 1)
            p = np.poly1d(coeffs)

            UW1 = p(Abfluss)
            UW2 = p(Q_con)
            # Calculate Mean Squared Error
            MSE = np.mean((Unterwasser - UW1) ** 2)
            # Calculate R-squared
            SSR = np.sum((Unterwasser - UW1) ** 2)
            SST = np.sum((Unterwasser - np.mean(UW1)) ** 2)
            R_squared = 1 - (SSR / SST)

        elif interpolation == 'quadratic':
            coeffs = np.polyfit(Abfluss, Unterwasser, 2)
            p = np.poly1d(coeffs)

            UW1 = p(Abfluss)
            UW2 = p(Q_con)
            # Calculate Mean Squared Error
            # MSE = np.mean((Unterwasser - UW1) ** 2)

            # Calculate R-squared
            SSR = np.sum((Unterwasser - UW1) ** 2)
            SST = np.sum((Unterwasser - np.mean(UW1)) ** 2)
            R_squared = 1 - (SSR / SST)

        elif interpolation == 'cubic':
            coeffs = np.polyfit(Abfluss, Unterwasser, 3)
            p = np.poly1d(coeffs)

            UW1 = p(Abfluss)
            UW2 = p(Q_con)
            # Calculate Mean Squared Error
            MSE = np.mean((Unterwasser - UW1) ** 2)
            # Calculate R-squared
            SSR = np.sum((Unterwasser - UW1) ** 2)
            SST = np.sum((Unterwasser - np.mean(UW1)) ** 2)
            R_squared = 1 - (SSR / SST)

        return UW2, R_squared

    def plot_interpolation(interpolation, Q_con, UW, Abfluss, Unterwasser, R_squared):
        # plt.close()
        plt.figure()
        plt.plot(Q_con, UW)
        plt.scatter(Abfluss, Unterwasser, color='red')
        plt.xlabel('Abfluss [m³/s]')
        plt.ylabel('UW [m ü. NHN]')
        plt.text(0.5, 0.9, f'R² ({interpolation}) = {R_squared:.3f}', transform=plt.gca().transAxes)
        if save_plot:
            plt.savefig(path + 'Q_UW_interpolation_{}.svg'.format(interpolation))
            plt.savefig(path + 'Q_UW_interpolation_{}.pdf'.format(interpolation))
        if show_plot:
            plt.show()

    Q_con = np.arange(0.1, np.max(Abfluss) + 0.5, 0.5)
    interpolation_types = ['exponential', 'linear', 'quadratic', 'cubic']
    plot_colors = ['black', 'green', 'brown', 'blue']

    plt.ioff()

    if interpolation == 'all':
        for i, interp_type in enumerate(interpolation_types):
            UW, R_squared = perform_interpolation(interp_type, Abfluss, Unterwasser, Q_con)
            plot_color = plot_colors[i % len(plot_colors)]
            plt.plot(Q_con, UW, color=plot_color)
            plt.scatter(Abfluss, Unterwasser, color='red')
            plt.xlabel('Abfluss [m³/s]')
            plt.ylabel('UW [m ü. NHN]')
            plt.text(0.5, 0.95 - i * 0.05, f'R² = {R_squared:.3f}', color=plot_color, transform=plt.gca().transAxes)
            plt.text(0.1, 0.95 - i * 0.05, f'Interpolation: {interp_type}', color=plot_color,
                     transform=plt.gca().transAxes)

        if save_plot:
            plt.savefig('Q_UW_interpolation_all.svg')

        if show_plot:
            plt.show()



    else:
        UW, R_squared = perform_interpolation(interpolation, Abfluss, Unterwasser, Q_con)
        plot_interpolation(interpolation, Q_con, UW, Abfluss, Unterwasser, R_squared)

    return UW


def operational_model(labyrinth_object, discharge_vector, downstream_water_level_vector, upstream_water_level_vector, interpolation_method, flap_gate_opject=None, design_upstream_water_level=None, max_flap_gate_angle=None,
                      fish_body_height=None, show_plot=False, save_plot=False, path=""):
    def check_and_exit_on_input_errors():
        def input_plausibilty(eingabe_name, eingabe_wert, max_value=None, min_value=None):
            fehler = []  # Store error messages

            if eingabe_wert is not None and eingabe_wert <= 0:
                if re.search(r'(Unterwasser|Oberwasser)', eingabe_name):
                    fehler.append(f"Achtung: {eingabe_name} Wert ist negative.")
                else:
                    fehler.append(f"{eingabe_name} Wert ist nicht plausibel (sollte größer als 0 sein).")

            if max_value is not None and eingabe_wert > max_value:
                fehler.append(f"{eingabe_name} Wert sollte {max_value} nicht überschreiten.")

            if min_value is not None and eingabe_wert < min_value:
                fehler.append(f"{eingabe_name} Wert sollte nicht kleiner sein als {min_value}.")

            return fehler  # Return list of fehler

        fehler = []  # Initialize the fehler list

        # Ensure vectors are not empty
        if len(discharge_vector) == 0:
            fehler.append("discharge_vector must not be empty.")
        if len(downstream_water_level_vector) == 0:
            fehler.append("downstream_water_level_vector must not be empty.")
        if len(upstream_water_level_vector) == 0:
            fehler.append("upstream_water_level_vector must not be empty.")

        # Check Abfluss values
        for i, abfluss_wert in enumerate(discharge_vector):
            fehler_abfluss = input_plausibilty("Abfluss " + str(discharge_vector[i]), abfluss_wert)
            fehler.extend(fehler_abfluss)

        for i, unterwasser_wert in enumerate(downstream_water_level_vector):
            fehler_unterwasser = input_plausibilty("Unterwasser " + str(downstream_water_level_vector[i]), unterwasser_wert)
            fehler.extend(fehler_unterwasser)

        for i, oberwasser_wert in enumerate(upstream_water_level_vector):
            fehler_oberwasser = input_plausibilty("Oberwasser " + str(upstream_water_level_vector[i]), oberwasser_wert)
            fehler.extend(fehler_oberwasser)

        # Ensure that all vectors have the same length (required for element-wise operations)
        if not (
            len(discharge_vector)
            == len(downstream_water_level_vector)
            == len(upstream_water_level_vector)
        ):
            fehler.append(
                "discharge_vector, downstream_water_level_vector and upstream_water_level_vector "
                "must have the same length."
            )

        # Check Stauziel, SohleHoehe, LabyrinthMaxBreite, LabyrinthMaxLaenge, and LabyrinthHoehe
        fehler += input_plausibilty("Stauziel", design_upstream_water_level)
        fehler += input_plausibilty("Klappe Winkel max", max_flap_gate_angle)
        fehler += input_plausibilty("Fishe Hoehe", fish_body_height)

        valid_interpolations = ["exponential", "linear", "quadratic", "cubic"]
        if interpolation_method not in valid_interpolations:
            fehler.append("Interpolationsmethode ist ungültig.")

        return fehler

    fehler = check_and_exit_on_input_errors()

    if all(message.startswith("Achtung:") for message in fehler):
        # Only warnings -> optionally print to console
        for i, fehler_message in enumerate(fehler, start=1):
            print(f"[operational_model] {i}. {fehler_message}")
        fehler = None
    else:
        # Hard input errors -> raise exception without additional print
        raise EngineerInputError(fehler)

    def operational_model_without_flap():

        Q_con = np.arange(0.1, np.max(discharge_vector) + 0.5, 0.5)
        # In server context we never want to open GUI windows; only save plots if explicitly requested.
        UW_con = UW_interpolation(
            discharge_vector,
            downstream_water_level_vector,
            interpolation_method,
            path=path,
            show_plot=show_plot,
            save_plot=save_plot,
        )
        Q_UW = np.stack((Q_con, UW_con), axis=1)

        Lab_upstream = np.zeros(np.size(Q_con))
        Lab_hu = np.zeros(np.size(Q_con))

        for i, (Q, UW) in enumerate(zip(Q_UW[:, 0], Q_UW[:, 1])):
            labyrinth_object.Q = Q
            labyrinth_object.UW = UW
            labyrinth_object.update()
            Lab_upstream[i] = labyrinth_object.yu
            Lab_hu[i] = labyrinth_object.hu

        def print_results():
            fig, ax = plt.subplots(3, sharex=True)

            ax[0].plot(Q_UW[:, 0], Q_UW[:, 1], color='r')
            ax[0].set_ylabel('UW [m ü. NHN]')
            ax[0].scatter(discharge_vector, downstream_water_level_vector)

            ax[1].plot(Q_UW[:, 0], Lab_upstream, label='Mit labyrinth')
            ax[1].scatter(discharge_vector, upstream_water_level_vector, label='Ohne Labyrinth')
            ax[1].set_ylabel('OW [m ü. NHN]')
            ax[1].legend()

            ax[2].plot(Q_UW[:, 0], Lab_hu)
            ax[2].set_ylabel('Oberfallhöhe [m]')
            ax[2].set_xlabel('Abfluss [m³/s]')

            if show_plot:
                fig.show()

            if save_plot:
                if path:
                    fig.savefig(path + '\\result.svg')
                    fig.savefig(path + '\\result.pdf')
                    fig.savefig(path + '\\result.png')
                else:
                    fig.savefig('result.svg')
                    fig.savefig('result.pdf')
                    fig.savefig('result.png')

        def save_results():
            # save results of all discharge values
            results_arr = np.stack((Q_con, UW_con, Lab_upstream, Lab_hu), axis=1)

            results_df = pd.DataFrame(results_arr, index=range(1, len(results_arr) + 1))
            results_col = ['Abfluss', 'UW', 'OW', 'Oberfallhöhe']
            results_df.columns = results_col

            results_df = results_df.round(2)

            # Skip CSV export in server mode
            if os.environ.get("SERVER_MODE") != "1":
                if path:
                    results_df.to_csv(path + '\\results.csv', sep=';', float_format='%.2f', header=results_col)
                else:
                    results_df.to_csv('results.csv', sep=';', float_format='%.2f', header=results_col)

            '''save the results for specific discahrge events'''

            # Get the first column (Abfluss values)
            abfluss_values = results_arr[:, 0]

            # Interpolate for each column based on Abfluss values
            results_events = np.zeros((len(discharge_vector), results_arr.shape[1]))
            for i in range(results_arr.shape[1]):
                f = interp1d(abfluss_values, results_arr[:, i])
                results_events[:, i] = f(discharge_vector)

            results_events_df = pd.DataFrame(results_events, index=range(1, len(results_events) + 1))
            results_events_col = ['Abfluss', 'UW', 'OW', 'Oberfallhöhe']
            results_events_df.columns = results_events_col
            results_events_df = results_events_df.round(2)

            # Skip CSV export in server mode
            if os.environ.get("SERVER_MODE") != "1":
                if path:
                    results_events_df.to_csv(path + '\\results_events.csv', sep=';', float_format='%.2f',
                                             header=results_events_col)
                else:
                    results_events_df.to_csv('results_events.csv', sep=';', float_format='%.2f',
                                             header=results_events_col)

            return results_df, results_events_df

        results, results_events = save_results()
        print_results()

        return results, results_events

    def operational_model_with_flap():
        Q_con = np.arange(0.1, np.max(discharge_vector) + 0.5, 0.5)
        SZ = design_upstream_water_level
        Klawinkel_Max = max_flap_gate_angle

        Klappe_al = np.zeros(np.size(Q_con))
        Abfluss_R = np.zeros(np.size(Q_con))
        Lab_Q = np.zeros(np.size(Q_con))
        Kla_Q = np.zeros(np.size(Q_con))
        Lab_upstream = np.zeros(np.size(Q_con))
        Kla_upstream = np.zeros(np.size(Q_con))

        Kla_hu = np.zeros(np.size(Q_con))
        Kla_vd = np.zeros(np.size(Q_con))

        P_new = np.zeros(np.size(Q_con))

        flap_gate_opject.Kalpha = 0

        UW_con = UW_interpolation(
            discharge_vector,
            downstream_water_level_vector,
            interpolation_method,
            path=path,
            show_plot=show_plot,
            save_plot=save_plot,
        )
        Q_UW = np.stack((Q_con, UW_con), axis=1)

        for i, (Q, UW) in enumerate(zip(Q_UW[:, 0], Q_UW[:, 1])):
            # =============================================================================
            #         alpha = np.arange(Kla.Kalpha, KlappeWinkel_max+0.2,0.2)
            #
            #         for j, al in enumerate(alpha):
            #
            #             Kla.Kalpha = al
            #             Kla.cal_P_neu()
            #             #print('Q =',Q,'Kla.P_neu=',Kla.P_neu,'Kla.Kalpha=',Kla.Kalpha)
            #
            #             kopplung(Q,UW,Lab,Kla)
            #
            #             if abs(Kla.yu - SZ) <= 0.01:
            #               break
            # =============================================================================

            def Objective_fn(Kalpha):
                flap_gate_opject.Kalpha = Kalpha
                flap_gate_opject.cal_P_neu()
                kopplung(Q, UW, labyrinth_object, flap_gate_opject)

                return abs(flap_gate_opject.yu - SZ)

            # initial values
            Kalpha0 = Klappe_al[i - 1] if i > 0 else [10]
            Kalpha_min = Klappe_al[i - 1] if i > 0 else 0

            # minmize function
            result = minimize_scalar(Objective_fn, Kalpha0, bounds=(Kalpha_min, Klawinkel_Max), method='bounded')

            Klappe_al[i] = result.x
            # print(result.x)

            Kla_upstream[i] = flap_gate_opject.yu

            Kla_hu[i] = flap_gate_opject.hu
            Kla_vd[i] = flap_gate_opject.vd

            Lab_upstream[i] = labyrinth_object.yu
            Abfluss_R[i] = labyrinth_object.Q / flap_gate_opject.Q
            Lab_Q[i] = labyrinth_object.Q
            Kla_Q[i] = flap_gate_opject.Q
            P_new[i] = flap_gate_opject.P_neu

        # return Q_con, Lab_Q, Kla_Q, Klappe_al, y_upstream

        def print_results():

            fig, ax = plt.subplots(4, sharex=True)

            ax[0].plot(Q_UW[:, 0], Q_UW[:, 1], color='r')
            ax[0].set_ylabel('UW [m ü. NHN]')
            ax[0].scatter(discharge_vector, downstream_water_level_vector)

            ax[1].plot(Q_UW[:, 0], Lab_Q, label='Labyrinth')
            ax[1].set_ylabel('Q Labyrinth [m³/s]')
            ax[1].plot(Q_UW[:, 0], Kla_Q, label='Klappe')
            ax[1].legend()
            ax[1].set_ylabel('Q [m³/s]')

            ax[2].plot(Q_UW[:, 0], Lab_upstream, marker='+', label='Labyrinth')
            ax[2].plot(Q_UW[:, 0], Kla_upstream, label='Klappe', color='c')
            ax[2].scatter(discharge_vector, upstream_water_level_vector, label='Ist')
            ax[2].legend()
            ax[2].set_ylabel('OW [m ü. NHN]')

            ax[3].plot(Q_UW[:, 0], Klappe_al, color='b')
            ax[3].set_ylabel(r'$\alpha$ [°]')

            # ax[4].plot(Q_UW[:,0],Kla_hu)
            # ax[4].set_ylabel('$h_{u,klappe}$[{\small m}]')
            # ax[4].axhline(y=0.68, color='red', linestyle='--')

            # ax[5].plot(Q_UW[:,0],Kla_vd)
            # ax[5].set_ylabel('$v_{d,klappe}$[{\small m²/s}]')
            # ax[5].set_xlabel('Abfluss [m³/s]') 

            # 3 * H fish text
            # ax[4].text(np.max(Abfluss)/2, 3*H_fische, '3 $\cdot$ $H_{Fisch}$',color='red')

            # Stauziel annotation
            kla_upstream = np.round(Kla_upstream, 3)
            constant_range = np.nonzero(kla_upstream <= design_upstream_water_level)
            const_range = constant_range[0]
            const_range_start = const_range[0]
            const_range_end = const_range[-1]

            # ax[2].annotate('', xy=(Q_UW[const_range_start, 0],Kla_upstream[0]+0.05), xytext=(Q_UW[const_range_end, 0],Kla_upstream[0]+0.05),
            # xycoords='data', textcoords='data',arrowprops={'arrowstyle': '|-|'})

            # ax[2].annotate('Stauziel', xy=((Q_UW[const_range_start, 0] + Q_UW[const_range_end, 0])/2,Kla_upstream[0]+0.1), ha='center', va='center')

            # Schwarz line
            ax[1].axvline(x=Q_UW[const_range_end, 0], color='k', linestyle='--')

            if show_plot:
                fig.show()

            if save_plot:
                if path:
                    fig.savefig(path + '\\result.svg')
                    fig.savefig(path + '\\result.pdf')
                    fig.savefig(path + '\\result.png')
                else:
                    fig.savefig('result.svg')
                    fig.savefig('result.pdf')
                    fig.savefig('result.png')

        def save_results():

            # save results of all discharge values
            results_arr = np.stack((Q_con, UW_con, Kla_upstream, Lab_Q, Kla_Q, Klappe_al), axis=1)

            results_df = pd.DataFrame(results_arr, index=range(1, len(results_arr) + 1))
            results_col = ['Abfluss', 'UW', 'OW', 'Labyrinth Q', 'Klappe Q', 'Klappe winkel']
            results_df.columns = results_col

            results_df = results_df.round(2)

            # Skip CSV export in server mode
            if os.environ.get("SERVER_MODE") != "1":
                if path:
                    results_df.to_csv(path + '\\results.csv', sep=';', float_format='%.2f', header=results_col)
                else:
                    results_df.to_csv('results.csv', sep=';', float_format='%.2f', header=results_col)

            '''save the results for specific discahrge events'''

            # Get the first column (Abfluss values)
            abfluss_values = results_arr[:, 0]

            # Interpolate for each column based on Abfluss values
            results_events = np.zeros((len(discharge_vector), results_arr.shape[1]))
            for i in range(results_arr.shape[1]):
                f = interp1d(abfluss_values, results_arr[:, i])
                results_events[:, i] = f(discharge_vector)

            results_events_df = pd.DataFrame(results_events, index=range(1, len(results_events) + 1))
            results_events_col = ['Abfluss', 'UW', 'OW', 'Labyrinth Q', 'Klappe Q', 'Klappe winkel']
            results_events_df.columns = results_events_col
            results_events_df = results_events_df.round(2)

            # Skip CSV export in server mode
            if os.environ.get("SERVER_MODE") != "1":
                if path:
                    results_events_df.to_csv(path + '\\results_events.csv', sep=';', float_format='%.2f',
                                             header=results_events_col)
                else:
                    results_events_df.to_csv('results_events.csv', sep=';', float_format='%.2f',
                                             header=results_events_col)

            return results_df, results_events_df

        results, results_events = save_results()
        print_results()

        return results, results_events

    if flap_gate_opject is None:
        results, results_events = operational_model_without_flap()
    else:
        results, results_events = operational_model_with_flap()

    return results, results_events


def tosbecken(Lab, Abfluss, Unterwasser, sicherheitsfaktor=25, Lab_Q=None, Kla=None, Kla_Q=None, Klappe_al=None):
    # plt.close()

    Q_UW = np.stack((Abfluss, Unterwasser), axis=1)
    sicherheitfaktor_initial = 0

    if Kla is not None:
        Lab_Q_UW = np.stack((Lab_Q, Q_UW[:, 1]), axis=1)
        Klappe_al = Klappe_al.to_numpy()
        Kla_Q_UW = np.stack((Kla_Q, Q_UW[:, 1]), axis=1)

    else:
        Lab_Q = Q_UW[:, 0]
        Lab_UW = Q_UW[:, 1]
        Lab_Q_UW = np.stack((Lab_Q, Lab_UW), axis=1)

    # Initialize arrays to store values
    delta_model = np.array([np.nan, np.nan])
    lange_tosbecken_model = np.array([np.nan, np.nan])
    y2_model = np.array([np.nan, np.nan])
    hd_model = np.array([np.nan, np.nan])
    ymax_3_model = np.array([np.nan, np.nan])

    j = 0  # Use 0 for Lab and 1 for Kla

    for model in [Lab, Kla]:

        if model == None:
            break

        if model == Lab:
            Q_UW = Lab_Q_UW
        elif model == Kla:
            Q_UW = Kla_Q_UW

        delta_all_model = np.full(np.size(Abfluss), np.nan)
        y2_all_model = np.full(np.size(Abfluss), np.nan)
        hd_all_model = np.full(np.size(Abfluss), np.nan)
        ymax_3_all_model = np.full(np.size(Abfluss), np.nan)
        lange_tosbecken_all_model = np.full(np.size(Abfluss), np.nan)

        for i, (Q, UW) in enumerate(zip(Q_UW[:, 0], Q_UW[:, 1])):

            if Q == 0:  # Skip the loop iteration if Q is zero
                continue
            model.Q = Q
            model.UW = UW
            model.update()

            if model == Kla:
                Kla.W = Kla.KW
                Kla.alpha = Klappe_al[i]
                Kla.P = Kla.KP

                Kla.update()
                Kla.Hu = Kla.hu + pow(Kla.v, 2) / (2 * Kla.g)

            # Define the function to be solved
            def f(y):
                if y <= 0:  # Check if y is positive
                    return 1e6
                v1 = Q / (model.W * y)
                H1 = y + pow(v1, 2) / (2 * model.g)

                return abs(model.Hu - H1)  # negate H1 to maximize instead of minimize

            y0 = 0.00001  #
            ymax = pow(pow(Q / model.W, 2) / model.g, (1 / 3))  # set maximum limit for y
            bounds = [(None, ymax)]  # set the upper bound constraint

            result = minimize(f, y0, bounds=bounds)
            y1 = result.x[0]

            v1 = Q / (model.W * y1)

            Fr1 = v1 / pow(model.g * y1, 0.5)

            y2 = 0.5 * y1 * (pow(1 + 8 * pow(Fr1, 2), 0.5) - 1)

            sicherheit_initial = 1 + sicherheitfaktor_initial / 100

            delta = (sicherheit_initial * y2) - (model.UW - model.Sh) + (pow(Q / model.W, 2) / (model.g * 2)) * (
                        (1 / pow(y2, 2)) - (1 / pow(model.UW - model.Sh, 2)))

            lange_tosbecken = 7 * (y2 - y1)  # Smetana

            # saving results
            delta_all_model[i] = delta
            y2_all_model[i] = y2
            hd_all_model[i] = model.UW - model.Sh
            ymax_3_all_model[i] = pow(Q / model.W, 2) / (model.g * 2)
            lange_tosbecken_all_model[i] = lange_tosbecken

        delta_model[j] = np.nanmax(delta_all_model)
        index_of_delta_max = np.nanargmax(delta_all_model)
        y2_model[j] = y2_all_model[index_of_delta_max]
        hd_model[j] = hd_all_model[index_of_delta_max]
        ymax_3_model[j] = ymax_3_all_model[index_of_delta_max]
        lange_tosbecken_model[j] = lange_tosbecken_all_model[index_of_delta_max]
        j += 1

        sicherheit = 1 + sicherheitsfaktor / 100

        delta_model_max_index = np.nanargmax(delta_model)

        if np.all(delta_model < 0):
            delta_design = np.nanmax(delta_model)
            lange_tosbecken_design = lange_tosbecken_model[delta_model_max_index]
        else:
            delta_design = (sicherheit * y2_model[delta_model_max_index]) - (hd_model[delta_model_max_index]) + \
                           ymax_3_model[delta_model_max_index] * ((1 / pow(y2_model[delta_model_max_index], 2)) - (
                        1 / pow(hd_model[delta_model_max_index], 2)))
            lange_tosbecken_design = lange_tosbecken_model[delta_model_max_index]

    return delta_design, lange_tosbecken_design


def plot_check_FAA_FAbA(Kla, results, results_events, fish_name=None, Bemessungsgeschwindigkeit=None):
    def check_fish_availability(fish_name):
        # Initialize variables to None
        fisch_lange = fisch_hohe = fisch_dicke = None
        min_bypass_breite = None

        if fish_name in fish_arten_DWA and fish_name in fish_arten_Ebel:
            fisch_lange, fisch_hohe, fisch_dicke = fish_arten_DWA[fish_name]
            min_bypass_breite = fish_arten_Ebel[fish_name]
            print(f"Die gewählte Fischart '{fish_name}' ist in der DWA und Ebel(2016) Quelle verfügbar.")
            print(
                f"Information von DWA: Fisch Länge = {fisch_lange}, Fisch Höhe = {fisch_hohe}, Fisch Dicke = {fisch_dicke}")
            print(f"Information von Ebel: Minimal Bypass Breite = {min_bypass_breite}")

        elif fish_name in fish_arten_DWA:
            fisch_lange, fisch_hohe, fisch_dicke = fish_arten_DWA[fish_name]
            print(f"Die gewählte Fischart '{fish_name}' ist in der DWA Quelle verfügbar aber nicht in Ebel(2016).")
            print(
                f"Information von DWA: Fisch Länge = {fisch_lange}, Fisch Höhe = {fisch_hohe}, Fisch Dicke = {fisch_dicke}")

        elif fish_name in fish_arten_Ebel:
            min_bypass_breite = fish_arten_Ebel[fish_name]
            print(f"Die gewählte Fischart '{fish_name}' ist in der Ebel(2016) Quelle verfügbar aber nicht in DWA")
            print(f"Information von Ebel: Minimal Bypass Breite = {min_bypass_breite}")

        return fisch_lange, fisch_hohe, fisch_dicke, min_bypass_breite

    # Example dictionaries
    fish_arten_DWA = {
        "Bachforelle": (0.5, 0.10, 0.05),
        "Äsche": (0.5, 0.10, 0.05),
        "Huchen": (1.0, 0.16, 0.12),
        "Seeforelle": (1.0, 0.21, 0.12),
        "Perlfisch": (0.7, 0.13, 0.07),
        "Döbel": (0.6, 0.16, 0.10),
        "Lachs": (1.0, 0.17, 0.10),
        "Meerforelle": (0.8, 0.17, 0.09),
        "Quappe": (0.6, 0.11, 0.11),
        "Plötze": (0.4, 0.13, 0.06),
        "Barbe": (0.7, 0.13, 0.08),
        "Nase": (0.6, 0.15, 0.09),
        "Zährte": (0.5, 0.13, 0.06),
        "Sterlet": (0.9, 0.15, 0.11),
        "Aland": (0.6, 0.18, 0.09),
        "Brachsen": (0.6, 0.21, 0.06),
        "Rapfen": (0.7, 0.15, 0.07),
        "Barsch": (0.4, 0.12, 0.07),
        "Hecht": (1.0, 0.14, 0.10),
        "Zander": (0.8, 0.15, 0.10),
        "Wels": (1.6, 0.26, 0.24),
        "Maifisch": (0.8, 0.16, 0.08),
        "Karpfen": (0.8, 0.24, 0.13),
        "Karausche": (0.45, 0.14, 0.07),
        "Schleie": (0.6, 0.16, 0.09),
        "Stör": (3.0, 0.51, 0.36),
        "Finte": (0.5, 0.10, 0.05),
        "Schnäpel": (0.4, 0.08, 0.04)
    }

    fish_arten_Ebel = {
        "Aale": 0.30,
        "Salmoníden": 0.45,
        "Salmoniden": 0.42,
        "Störe": 1.00,
        "Neurıaugen": 0.30,
        "Aland": 0.36,
        "Äsche": 0.30,
        "Bachforelle": 0.34,
        "Barbe": 0.38,
        "Brasse": 0.34,
        "Döbel": 0.35,
        "Elritze": 0.17,
        "Flussbarsch": 0.30,
        "Hasel": 0.24,
        "Hecht": 0.34,
        "Huchen": 0.42,
        "Karpfen": 0.47,
        "Nase": 0.31,
        "Plötze": 0.26,
        "Quappe": 0.40,
        "Rapfen": 0.36,
        "Ukelei": 0.21,
        "Wels": 0.58,
        "Zährte": 0.31,
        "Zander": 0.39
    }

    # Check if fish_name is in either fish_arten_DWA or fish_arten_Ebel
    if fish_name not in fish_arten_DWA and fish_name not in fish_arten_Ebel:
        print(f"Die gewählte Fischart '{fish_name}' ist in der DWA und Ebel(2016) Quelle nicht verfügbar.")
        return

    fisch_lange, fisch_hohe, fisch_dicke, min_bypass_breite = check_fish_availability(fish_name)

    # Convert fish_arten dictionary to DataFrame
    # fish_df_DWA = pd.DataFrame.from_dict(fish_arten_DWA, orient='index', columns=['Fisch Länge', 'Fisch Höhe', 'Fisch Dicke'])
    # fish_df_Ebel = pd.DataFrame.from_dict(fish_arten_Ebel, orient='index', columns=['Minimal bypass breite'])

    Klappe_hu = np.zeros(len(results))
    Klappe_hd = np.zeros(len(results))
    Klappe_a = np.zeros(len(results))
    Klappe_P = np.zeros(len(results))
    delta_h = np.zeros(len(results))
    v_FAA = np.full(len(results), Bemessungsgeschwindigkeit)
    v_FAbA = np.zeros(len(results))

    for i, (Q, UW, klappe_w) in enumerate(zip(results.iloc[:, 4], results.iloc[:, 1], results.iloc[:, -1])):
        Kla.Q = Q
        Kla.UW = UW
        Kla.Kalpha = klappe_w
        Kla.cal_P_neu()
        Kla.update()
        Klappe_P[i] = Kla.P_neu
        Klappe_hu[i] = Kla.hu
        Klappe_hd[i] = Kla.hd
        Klappe_a[i] = Kla.beschleunigung
        delta_h[i] = results.iloc[i, 2] - results.iloc[i, 1]
        v_FAbA[i] = results.iloc[i, 4] / ((results.iloc[i, 1] - Kla.Sh) * Kla.KW)

    delta_h_wasserpolster = np.maximum(delta_h * 0.25, 1.2)

    anforderungen = [
        1.0,
        min_bypass_breite,
        9 * fisch_dicke if fisch_dicke is not None else None,
        3 * fisch_hohe if fisch_hohe is not None else None,
        8,
        delta_h_wasserpolster,
        Klappe_P
    ]

    ergebniss = [
        Klappe_a,
        Kla.KW,
        Kla.KW,
        Klappe_hu,
        pow((2 * 9.81 * delta_h), 0.5),
        results.iloc[:, 1] - Kla.Sh,
        results.iloc[:, 1] - Kla.Sh + 0.5,
        results.iloc[:, 1] - Kla.Sh,
        v_FAA,
        v_FAbA
    ]

    # Labels for subplots
    y_labels = [
        'Beschleunigung [m/s pro m]',
        'Breite der Klappe [m]',
        '$h_{u,klappe}$[{\small m}]',
        'Eintauchgeschwindigkeit [m/s]',
        '$h_{uw}$[{\small m}]',
        'KlappenOberkante [m]'
    ]

    subplot_titles = [
        'Geschwindigkeitsänderung über die Klappenlänge',
        'Mindestbreite der Klappe',
        'Überfallhöhe an der Klappe',
        'Eintauchgeschwindigkeit',
        'Anforderungen an das Wasserpolster im UW',
        'Einleitung des Wassers am Ende des Kanals '
    ]
    # Event_lables = ["Q5", "Q30", "MQ", "Q330", "MHQ", "Q360", "HQ5", "HQ10", "HQ20", "HQ50", "HQ100"]
    Event_lables = ["Q5", "Q30", "MQ", "Q330"]

    # Create a figure with subplots
    fig, ax = plt.subplots(7, 1, figsize=(10, 16))  # 2 rows, 1 column

    # Plot for the second subplot (results.iloc[:, 0] vs ergebniss[0])
    ax[0].plot(results.iloc[:, 0], ergebniss[0])
    ax[0].axhline(y=anforderungen[0], color='r', linestyle='--')
    ax[0].set_ylabel(y_labels[0])
    ax[0].set_title(subplot_titles[0])

    # Plot for the first subplot (ergebniss[1] vs anforderungen[1])
    if anforderungen[1] is not None:
        ax[1].axhline(y=anforderungen[1], color='r', linestyle='--')
        # Ebel (2016)
        ax[1].text(results.iloc[:, 0].max() / 2, anforderungen[1], 'Ebel (2016)', color='red')
    else:
        ax[1].text(results.iloc[:, 0].max() / 2, anforderungen[2] / 2 + 1,
                   'Die gewählte Fischart ist nicht verfügbar im Ebel (2016)', color='red')

    if anforderungen[2] is not None:
        ax[1].axhline(y=anforderungen[2], color='r', linestyle='--')
        # 9 * H fish text
        ax[1].text(results.iloc[:, 0].max() / 2, anforderungen[2], '9 $\cdot$ $D_{Fisch}$', color='red')
    else:
        ax[1].text(results.iloc[:, 0].max() / 2, ergebniss[2] / 2,
                   'Die gewählte Fischart ist nicht verfügbar im DWA (2014)', color='red')

    ax[1].axhline(y=ergebniss[2], xmin=0, xmax=results.iloc[:, 0].max(), linestyle='-')
    ax[1].set_ylabel(y_labels[1])
    ax[1].set_xlim([0, results.iloc[:, 0].max()])
    ax[1].set_title('Klappenbreite')

    ax[2].plot(results.iloc[:, 0], ergebniss[3])
    if anforderungen[2] is not None:
        ax[2].axhline(y=anforderungen[3], color='red', linestyle='--')
        # 3 * H fish text
        ax[2].text(results.iloc[:, 0].max() / 2, anforderungen[3], '3 $\cdot$ $H_{Fisch}$', color='red')
    else:
        ax[2].text(results.iloc[:, 0].max() / 2, ax[2].get_ylim()[1] / 2,
                   'Die gewählte Fischart ist nicht verfügbar im DWA (2014)', color='red')

    ax[2].set_ylabel(y_labels[2])
    ax[2].set_title(subplot_titles[2])

    ax[3].plot(results.iloc[:, 0], ergebniss[4])
    ax[3].axhline(y=anforderungen[4], color='red', linestyle='--')
    ax[3].set_ylabel(y_labels[3])
    ax[3].set_title(subplot_titles[3])

    ax[4].plot(results.iloc[:, 0], ergebniss[5], label='$h_{uw}$')
    ax[4].plot(results.iloc[:, 0], anforderungen[5], label='max(0.25 $\cdot$ Fallhöhe, 1.2)', color='r', linestyle='--')
    ax[4].set_ylabel(y_labels[4])
    ax[4].set_title(subplot_titles[4])
    ax[4].legend(loc='upper right')

    ax[5].plot(results.iloc[:, 0], ergebniss[6], label='$h_{uw}$+ 0.5[m]')
    ax[5].plot(results.iloc[:, 0], ergebniss[5], label='$h_{uw}$')
    ax[5].plot(results.iloc[:, 0], anforderungen[6], label='Oberkante der Klappe über der Sohle')
    ax[5].set_ylabel(y_labels[5])
    ax[5].set_title(subplot_titles[5])
    ax[5].legend(loc='upper right')

    ax[6].plot(results.iloc[:, 0], ergebniss[8], label='$v_{FAA}$')
    ax[6].plot(results.iloc[:, 0], ergebniss[9], label='$v_{FAbA}$')
    ax[6].set_xlabel('Abfluss [m³/s]')
    ax[6].set_ylabel('Geschwindigkeit [m/s]')
    ax[6].legend(loc='upper right')
    ax[6].set_title('Fließgeschwindigkeiten am Einsteig der FAA bzw. im Unterwasser der FAbA')

    # Add a secondary x-axis on the top
    secax = ax[0].secondary_xaxis('top')
    secax.set_xticks(results_events.iloc[:4, 0])
    secax.set_xticklabels(Event_lables, rotation=90, color='red')
    secax.tick_params(axis='x', labelsize=8)

    # Adjust the position of the secondary axis
    secax.spines['bottom'].set_position(('outward', 10))

    fig.suptitle('Anforderungen an den Bypass aus Sicht des Abstiegs und des Aufstiegs', fontsize=16)

    for event in results_events.iloc[:4, 0]:
        for axs in ax:
            axs.axvline(x=event, color='b', linestyle='--', alpha=0.3)

    for axs in ax:
        axs.set_xlim(left=0)
        axs.set_ylim(bottom=0)

    # Display the plot
    plt.subplots_adjust(hspace=0.35)
    plt.subplots_adjust(top=0.93)
    plt.grid(True)  # Add grid if needed
    plt.show()
    plt.savefig('check_FAbA_FAA.png')


# Export Geometry Parameters according to Pralong et al. 2011 or Tullis 20XX
# for further usage in e.g. automatic CAD geometry generation
def write_lab_excel(lab):
    # SI-Units
    data = {
        "W": lab.W,  # width
        "B": lab.B,  # length
        "P": lab.P,  # height including crest
        "Ts": lab.t,  # thickness
        "alpha": lab.alpha,  # sidewall angle
        "L": lab.L,  # developed length
        "N": lab.N,  # number of keys
        "D": lab.D,  # front wall length
        "w": lab.w,  # key width
        "S": lab.S  # overall additional wall width
    }

    columns = list(data.keys())
    values = list(data.values())
    row_numbers = list(range(len(columns)))

    # DataFrame vorbereiten
    df = pd.DataFrame([values], columns=columns)

    # Laufnummern und Spaltennamen manuell schreiben
    with pd.ExcelWriter("labyrinth.xlsx", engine="openpyxl") as writer:
        # Erst Laufnummern
        pd.DataFrame([row_numbers]).to_excel(writer, index=False, header=False, startrow=0)
        # Dann Spaltennamen + Werte
        df.to_excel(writer, index=False, startrow=1)


def write_flap_excel(flap):
    data = {
        'width': flap.KW,
        'height': flap.KP,
        'angle': flap.Kalpha
    }

    columns = list(data.keys())
    values = list(data.values())
    row_numbers = list(range(len(columns)))

    # DataFrame vorbereiten
    df = pd.DataFrame([values], columns=columns)

    # Laufnummern und Spaltennamen manuell schreiben
    with pd.ExcelWriter("flap.xlsx", engine="openpyxl") as writer:
        # Erst Laufnummern
        pd.DataFrame([row_numbers]).to_excel(writer, index=False, header=False, startrow=0)
        # Dann Spaltennamen + Werte
        df.to_excel(writer, index=False, startrow=1)