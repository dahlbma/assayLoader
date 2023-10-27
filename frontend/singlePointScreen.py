import re, sys, os, logging, glob
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5.QtGui import QIntValidator
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

        #self.inputFiles_tab.setReadOnly(True)

        saInstruments = dbInterface.getInstruments(self.token)
        saInstruments = [""] + saInstruments
        self.instrument_cb.addItems(saInstruments)
        self.instrument_cb.currentIndexChanged.connect(self.instrumentChange)
        
        self.dataColumn_eb.editingFinished.connect(self.checkDataColumn)
        self.rawDataDir_btn.clicked.connect(self.selectRawDataDir)

        self.runQc_btn.setDisabled(True)
        self.runQc_btn.setEnabled(True)
        self.runQc_btn.clicked.connect(self.runQc)

        self.outputFile_eb.editingFinished.connect(self.checkDataColumn)

        self.posCtrl_eb.editingFinished.connect(self.checkDataColumn)
        self.posCtrl_eb.setText('CTRL')

        self.negCtrl_eb.editingFinished.connect(self.checkDataColumn)
        self.negCtrl_eb.setText('DMSO')

        int_validator = QIntValidator()
        self.hitThreshold_eb.setValidator(int_validator)
        
        self.platemapFile_btn.clicked.connect(self.selectPlatemap)
        self.platemapFile_lab.setText('')

        self.rawDataDir_lab.setText('')
        self.outputFile_lab.setText('')
        self.generateQCinput_btn.setDisabled(True)

        self.form_values = {
            "instrument": False,
            "raw_data_column": False,
            "raw_data_directory": False,
            "platemap_file": False,
            "pos_ctrl": False,
            "neg_ctrl": False,
            "qc_output_file": False
        }


    def checkForm(self):
        #print(self.form_values)
        if all(self.form_values.values()):
            self.runQc_btn.setEnabled(True)
        else:
            self.runQc_btn.setDisabled(True)
            self.runQc_btn.setEnabled(True)

    def checkDataColumn(self):
        self.checkForm()
        # Read a csv file from the inputFiles_tab text box and see of the datacolumn in this eb is present
        pass

    
    def getInputFilesFromTab(self):
        saFiles = []

        for row in range(self.inputFiles_tab.rowCount()):
            item = self.inputFiles_tab.item(row, 0)  # Get item in the first column
            if item is not None:
                saFiles.append(item.text())
        return saFiles


    def addFileToTable(self, sFile):
        row_position = self.inputFiles_tab.rowCount()  # Get the current row count
        self.inputFiles_tab.insertRow(row_position)  # Insert a new row at the end

        fileItem = QTableWidgetItem(sFile)
        statusItem = QTableWidgetItem("Unknown")
        self.inputFiles_tab.setItem(row_position, 0, fileItem)
        self.inputFiles_tab.setItem(row_position, 1, statusItem)


    def selectRawDataDir(self):
        self.inputFiles_tab.setRowCount(0)
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly  # Set the option to allow selecting directories only

        directory = QFileDialog.getExistingDirectory(
            None, "Select Directory", options=options
        )
        self.rawDataDir_lab.setText(directory)
        csv_files = glob.glob(os.path.join(directory, '*.[cC][sS][vV]'))

        sFiles = ''
        for csv_file in csv_files:
            self.addFileToTable(os.path.basename(csv_file))
        self.form_values['raw_data_directory'] = True
        self.checkForm()


    def selectPlatemap(self):
        options = QFileDialog.Options()
        platemap, _ = QFileDialog.getOpenFileName(
            None, "Open File", "", "All Files (*);;CSV Files (*.csv)", options=options
        )

        if platemap:
            print(f"Selected file: {platemap}")
            self.platemapFile_lab.setText(os.path.basename(platemap))
            self.form_values['platemap_file'] = True
        self.checkForm()


    def instrumentChange(self):
        sInstrument = self.instrument_cb.currentText()
        saInstrument, iAllOk = dbInterface.getInstrument(self.token, sInstrument)
        if iAllOk:
            self.dataColumn_eb.setText(saInstrument[0]['data_col'])
            #self.posCtrl_eb.setText()
            #self.negCtrl_eb.setText()

    def runQc(self):
        print('running qc')
        sDir = self.rawDataDir_lab.text()
        saFiles = self.getInputFilesFromTab()
        parseEnvision.generateIndata(sDir, saFiles)

