import re, sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import openpyxl
import csv
from pathlib import Path

from assaylib import *

class SinglePointScreen(QMainWindow):
    def __init__(self, token, test):
        super(SinglePointScreen, self).__init__()
        self.token = token
        self.mod_name = "loader"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/sp.ui"), self)
        
        self.inputFiles_te.setReadOnly(True)
        saInstruments = dbInterface.getInstruments(self.token)

        print(type(saInstruments))
        self.instrument_cb.addItems(saInstruments)
