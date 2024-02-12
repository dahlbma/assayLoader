import re, sys, os, logging, glob, csv
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QDate, QUrl, QRegExp
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QComboBox, QDateEdit
from PyQt5 import QtGui
from PyQt5.QtGui import QIntValidator, QBrush, QColor, QValidator, QRegExpValidator
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import openpyxl
from pathlib import Path
from instruments import parseEnvision
import pandas as pd
import subprocess
from z_factor import *
from assaylib import *
from prepareHarmonyFile import *
import platform
from inhibitionScatter import ScatterPlotWindow


# Get the operating system name
os_name = platform.system()

class DoseResponseScreen(QMainWindow):
    from assaylib import gotoSP
    def __init__(self, token, test):
        super(DoseResponseScreen, self).__init__()
        self.token = token
        self.mod_name = "loader"
        self.logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/doseResponseTab.ui"), self)
        self.rVolume = None
        
        self.finalWellVolumeMicroliter_eb.textChanged.connect(self.wellVolumeChanged)

        regex = QRegExp("[0-9]+.?[0-9]*")  # Only digits 1-9 and a single dot
        validator = QRegExpValidator(regex, self.finalWellVolumeMicroliter_eb)
        self.finalWellVolumeMicroliter_eb.setValidator(validator)

        self.selectHarmonyDirectory_btn.setEnabled(False)
        self.selectHarmonyDirectory_btn.clicked.connect(self.selectHarmonyDirectory)

        self.goto_sp_btn.clicked.connect(self.gotoSP)


    def wellVolumeChanged(self, sVolume):
        try:
            self.rVolume = float(sVolume)
        except:
            self.selectHarmonyDirectory_btn.setEnabled(False)
            self.rVolume = None
            return
        self.selectHarmonyDirectory_btn.setEnabled(True)
        

    def generatePlatemap(self):
        print('generate platemap here')
        #self.generateCurvefittingInput_btn.setEnabled(True)


    def selectHarmonyDirectory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog  # Use the native file dialog
        directory_dialog = QFileDialog()
        directory_dialog.setOptions(options)
        # Set the file mode to DirectoryOnly to allow selecting directories only
        directory_dialog.setFileMode(QFileDialog.DirectoryOnly)
        # Show the directory dialog
        selected_directory = directory_dialog.getExistingDirectory(self, 'Open Directory', '')

        subdirectory_path = os.path.join(selected_directory, "preparedHaronyFiles")
        if subdirectory_path == "preparedHaronyFiles":
            return

        if selected_directory:
            #self.generatePlatemap_btn.setEnabled(True)
            pass
        #self.generateCurvefittingInput_btn.setEnabled(False)

        findHarmonyFiles(self, subdirectory_path, selected_directory)       
        

    def generateCurvefittingInput(self):
        print('generate curvefitting input here')
        

        
'''
selectHarmonyDirectory_btn
generatePlatemap_btn
generateCurvefittingInput_btn
'''
