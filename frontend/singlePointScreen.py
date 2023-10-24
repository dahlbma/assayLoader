import re, sys, os, logging, glob
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import openpyxl
import csv
from pathlib import Path
from instruments import parseEnvision

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
        self.instrument_cb.addItems(saInstruments)
        
        self.dataColumn_eb.editingFinished.connect(self.checkDataColumn)

        self.rawDataDir_btn.clicked.connect(self.selectRawDataDir)

        self.runQc_btn.setDisabled(True)

        self.outputFile_eb.editingFinished.connect(self.checkDataColumn)
        self.posCtrl_eb.editingFinished.connect(self.checkDataColumn)
        self.negCtrl_eb.editingFinished.connect(self.checkDataColumn)
        self.platemapFile_btn.clicked.connect(self.selectPlatemap)
        self.platemapFile_lab.setText('')
        
        

    def checkDataColumn(self):
        # Read a csv file from the inputFiles_te text box and see of the datacolumn in this eb is present
        pass

    def selectRawDataDir(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly  # Set the option to allow selecting directories only

        directory = QFileDialog.getExistingDirectory(
            None, "Select Directory", options=options
        )
        self.rawDataDir_lab.setText(directory)
        csv_files = glob.glob(os.path.join(directory, '*.[cC][sS][vV]'))

        sFiles = ''
        for csv_file in csv_files:
            sFiles += f'\n{os.path.basename(csv_file)}'
        self.inputFiles_te.setText(sFiles.lstrip())

    
        parseEnvision.generateIndata(directory)
