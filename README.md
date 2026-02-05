# Komstor.py
Tool for administring component storage
This program is created by Roeland Riemens with help of chatgpt.
free of use if you want to

Install python3 latest version first if you want to run this program
needed libraries:

import tkinter as tk
from tkinter import ttk
import sqlite3
import webbrowser
import os
import shutil
from datetime import datetime
import sys


When program gives an error at import install missing libraries

The used storage cabinet has 128 drawers with id (LOKATIE) A1A, A1B, A2A .... P8A, P8B
When first started in a folder with no database it creates an empty sqlite database with all these locations already filled in. Make sure there is a subfolder "backup" in the program folder, so backups can be made as many as you want.
You cannot add new locations with this program.
Use SQLite studio if you want to add records with new locations. Field Compnr is same as Naam, except that only numbers are filled in. So when you search an 74LS00 you can als search for 7400. When I fill in database I only type full Naam in both fields (copy paste with ctrl-c ctrl-v), and later on run the correctie_compnr.sql in SQLite studio to convert to only numbers.

When stock is low color in browser changes from white to yellow, and when empty red. When OPSLAAN (save) is blue, changes are not save to database. When you want to enter a new component, and it can't be found it shows an empty browser. First clear search (zoek) box and scroll until you find a red, empty location. select this before typing in otherwise there is no location and you can't save it.

When you want to delete an empty record, the (Wis record) is available only when stock is 0. 

Copy/paste with mouse is not available.

Zoek searches in all fields.
URL: when you fill in a complete URL, with Open URL butten you can get more info of the component entered. For instance https://www.mouser.com/datasheet/2/302/HEF40174B-88493.pdf

Sorry for bad english,
with kind regards, Roeland Riemens 05 feb 2026
