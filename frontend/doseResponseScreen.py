import re, sys, os, logging, glob, csv
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QComboBox, QDateEdit
from PyQt5.QtCore import Qt, QDate, QUrl
from PyQt5 import QtGui
from PyQt5.QtGui import QIntValidator, QBrush, QColor, QValidator, QDoubleValidator
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

        self.generatePlatemap_btn.setEnabled(False)
        self.generatePlatemap_btn.clicked.connect(self.generatePlatemap)
        self.generateCurvefittingInput_btn.setEnabled(False)
        self.generateCurvefittingInput_btn.clicked.connect(self.generateCurvefittingInput)
        self.selectHarmonyDirectory_btn.clicked.connect(self.selectHarmonyDirectory)

        self.goto_sp_btn.clicked.connect(self.gotoSP)


    def generatePlatemap(self):
        print('generate platemap here')
        self.generateCurvefittingInput_btn.setEnabled(True)


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
            self.generatePlatemap_btn.setEnabled(True)
        self.generateCurvefittingInput_btn.setEnabled(False)

        print(subdirectory_path)
        findHarmonyFiles(self, subdirectory_path, selected_directory)       
        

    def generateCurvefittingInput(self):
        print('generate curvefitting input here')
        

        
'''
selectHarmonyDirectory_btn
generatePlatemap_btn
generateCurvefittingInput_btn
'''