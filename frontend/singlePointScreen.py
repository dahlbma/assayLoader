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
import pandas as pd


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
        self.fileToPlateMap_btn.clicked.connect(self.selectFileToPlateMap)
        
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
        self.platemapDf = None

        self.fileToPlate_lab.setText('')
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


    def readPlateMap(sPlateId, dfPlatemap):
        new_df = dfPlatemap[dfPlatemap.iloc[:, 0] == sPlateId]
        return new_df

        
    def getDataStart(self, file, sDataColumn):
        saLines = file.readlines()
        iDataColPosition = None
        iWellColPosition = None
        saDataLines = None
        iNrOfCols = 0
        iLineNumber = 0
        
        for line in saLines:
            saLine = line.split(',')
            iLineNumber += 1
            if 'Well' in saLine:
                iNrOfCols = len(saLine)
                iDataColPosition = saLine.index(sDataColumn)
                iWellColPosition = saLine.index('Well')
                saDataLines = saLines[iLineNumber:]
                iLineNumber = 0
                break

        if saDataLines == None:
            return iDataColPosition, iWellColPosition, saDataLines

        for line in saDataLines:
            iLineNumber += 1
            saLine = line.split(',')
            if len(saLine) != iNrOfCols:
                saDataLines = saDataLines[:iLineNumber-1]
                ii = 0
                for i in saDataLines:
                    ii += 1
                    print(ii, i)
                quit()
            
        return saLines[iLineNumber:], iDataColPosition, iWellColPosition


    def selectFileToPlateMap(self):
        self.inputFiles_tab.setRowCount(0)
        
        file_path, _ = QFileDialog.getOpenFileName(None, "Open File", "", "All Files (*);;Text Files (*.txt)")
        df = pd.read_excel(file_path)
        self.fileToPlate_lab.setText(file_path)
        plate_file_dict = df.set_index('plate')['file'].to_dict()

        path_to_data_dir = os.path.dirname(file_path)
                
        sFiles = ''
        for row, (plate, sFile) in enumerate(plate_file_dict.items()):
            self.addFileToTable(sFile)
            print(sFile)

            full_path = os.path.join(path_to_data_dir, sFile)
            with open(full_path, 'r') as file:
                sDataLines = self.getDataStart(file, self.dataColumn_eb.text())
                
            print(self.dataColumn_eb.text())
            print(sDataLines)
            quit()
        
        self.form_values['raw_data_directory'] = True
        self.checkForm()


    def selectPlatemap(self):
        options = QFileDialog.Options()
        platemap, _ = QFileDialog.getOpenFileName(
            None, "Open File", "", "All Files (*);;CSV Files (*.csv)", options=options
        )

        if platemap:
            self.platemapDf = pd.read_excel(platemap)
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
        sFileToPlate = self.fileToPlate_lab.text()
        saFiles = self.getInputFilesFromTab()
        parseEnvision.generateIndata(sFileToPlate, saFiles)

