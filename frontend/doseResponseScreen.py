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

        self.goto_sp_btn.clicked.connect(self.gotoSP)
