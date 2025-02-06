# ENGINEER
Welcome to the ENGINEER project (**En**twicklun**g** standardisierter **In**formationsmodelle für die Planung am B**e**ispiel von Labyrinth-W**e**h**r**anlagen)!

The ENGINEER project is developing an automated digital design for labyrinth weir structures. The project was funded by [mFUND](https://bmdv.bund.de/DE/Themen/Digitales/mFund/Projekte/mfund-projekte.html). Participants include the [BAW](www.baw.de), [WNA Magdeburg](https://www.wna-magdeburg.wsv.de/Webs/WNA/WNA-Magdeburg/DE/Startseite/startseite_node.html), [Arcadis](https://www.arcadis.com/de-de) and [Cadcom](https://cadcom.de/).

This repository contains the Python scripts for the hydraulic design of labyrinth weir structures developed by BAW.

## Usage
### General considerations
This development can be used to design labyrinth weir structures consisting of a labyrinth weir and a parrallel flap gate. Furthermore, it is possible to estimate the hydraulic effect of the system over a given discharge spectrum. You can find more information about labyrinth weirs in the [BAWMitteilungen Nr. 105](https://hdl.handle.net/20.500.11970/107132).<br>
This repository consists of two Python files, among other things:
* <pre>engineer.py</pre> This ist the brain. You should not modify this file unless you find an bug or want to further develop the project.
* <pre>example.py</pre> This is an usage example. Feel free to adapt this file according to your wishes and your project.

### Required Python libraries
You need to have installed the following python libraries on your system:
<pre>numpy matplotlib os shutil pandas math re sys winreg scipy</pre>
We recommend installing it either with pip or conda.<br><br>
Example with pip:
<pre>pip install numpy matplotlib os shutil pandas math re sys winreg scipy</pre>
Example with conda:
<pre>conda install numpy matplotlib os shutil pandas math re sys winreg scipy</pre>

### Hydraulic Design
#### Case 1: You already know the geometry of your labyrinth weir
If you already know the geometry of your labyrinth weir you can plot it and calculate the upstream water level depending on the geometry, the discharge and the donwstream water level.
<pre>
  lab = labyrinth(  bottom_height=0.1,                          #bottom height [m]  
                    downstream_water_level=1.09,                #downstream Water level [m]
                    Q=10,                                       #discharge [m3/s]
                    labyrinth_width=15,                         #labyrinth weir width [m]
                    labyrinth_height=2.2,                       #labyrinth weir height [m]
                    labyrinth_length=8,                         #labyrinth weir length in flow direction [m]
                    key_angle=8,                                #key angle [degree]
                    D=0.5)                                      #front wall width [m]
</pre>
Now, the object `lab` from the class `labyrinth` is initialized and the upstream water level is calculated.<br>
The overflow height `lab.hu`, or the absolute upstream water level `lab.yu` are now atributes of the objcet `lab`. In case that you change any atribut, e.g. the labyrinth weir 
height `lab.P` you have to rerun the hydraulic calculation with `lab.update()`.<br>
Furthermor you can get a text output of the calculation:
<pre>
  lab.verbose = 1
  lab.print_results()

  Key Laenge = 8.00 [m] 
  Key Frontwand = 0.5 [m]
  Key Winkel = 8 [°]
  Key Wandstaerke = 0.3 [m]
  Key Hoehe = 2.20 [m]
  Key Anzahl = 4 
  Key Weite = 3.25 [m] 
  Keys Weite = 12.99 [m] 
  Seite Weite[S] = 2.01 [m] 
  Wehr weite = 15.00 [m] 
  L/W = 4.71 [m] 
  Hu = 0.18 [m] 
  hu = 0.17 [m] 
  Kein Rückstaueinfluss! 
</pre>
  
