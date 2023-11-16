import re, sys, os, logging, glob
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QComboBox, QDateEdit
from PyQt5.QtCore import Qt, QDate
from PyQt5 import QtGui
from PyQt5.QtGui import QIntValidator, QBrush, QColor
import openpyxl
from pathlib import Path
from instruments import parseEnvision
import pandas as pd
import subprocess
from z_factor import *
from assaylib import *
from prepareHarmonyFile import *
import platform

# Get the operating system name
os_name = platform.system()

class SinglePointScreen(QMainWindow):
    def __init__(self, token, test):
        super(SinglePointScreen, self).__init__()
        self.token = token
        self.mod_name = "loader"
        self.logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/singlePointTab.ui"), self)

        #####################
        # Prep data screen
        self.prepareHarmony_btn.clicked.connect(self.prepareHarmonyFiles)
        #self.nrOfPlateCopies_sp           # spin box
        #self.plates_te.                   # text edit
        self.printPlates_btn.clicked.connect(self.printPlates)
        # Prep data screen end
        #####################

        self.dataColumn_cb.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        saInstruments = dbInterface.getInstruments(self.token)
        saInstruments = [""] + saInstruments
        self.instrument_cb.addItems(saInstruments)
        self.instrument_cb.currentIndexChanged.connect(self.instrumentChange)
        
        #self.dataColumn_cb.editingFinished.connect(self.checkDataColumn)
        self.fileToPlateMap_btn.clicked.connect(self.selectFileToPlateMap)
        self.fileToPlateMap_btn.setDisabled(True)
        
        self.runQc_btn.setDisabled(True)
        self.runQc_btn.clicked.connect(self.runQc)

        self.generateQcInput_btn.setDisabled(True)
        self.generateQcInput_btn.clicked.connect(self.generateQcInput)
        
        self.outputFile_eb.editingFinished.connect(self.checkDataColumn)
        self.outputFile_eb.setText('screenQC.xlsx')

        self.posCtrl_eb.editingFinished.connect(self.checkDataColumn)
        self.posCtrl_eb.setText('CTRL')

        self.negCtrl_eb.editingFinished.connect(self.checkDataColumn)
        self.negCtrl_eb.setText('DMSO')

        int_validator = QIntValidator()
        self.hitThreshold_eb.setValidator(int_validator)
        
        self.platemapFile_btn.clicked.connect(self.selectPlatemap)
        self.platemapFile_lab.setText('')

        #############################################
        ##### GLOBALS
        self.platemapDf = None
        self.plate_file_dict = None
        self.fileToPlatemapFile = None
        ##### END GLOBALS
        #############################################
        
        self.fileToPlate_lab.setText('')
        self.qcInputFile_lab.setText('')

        self.populateScreenData()
        
        self.form_values = {
            "instrument": False,
            "raw_data_column": False,
            "raw_data_directory": False,
            "platemap_file": False,
            "pos_ctrl": False,
            "neg_ctrl": False,
            "qc_output_file": False
        }


    def populateScreenData(self):
        saProjects = dbInterface.getProjects(self.token)
        self.project_cb.addItems(saProjects)

        saOperators = dbInterface.getOperators(self.token)
        self.operator_cb.addItems(saOperators)

        saTargets = dbInterface.getTargets(self.token)
        self.target_cb.addItems(saTargets)

        saAssayType = dbInterface.getAssayTypes(self.token)
        self.assayType_cb.addItems(saAssayType)

        saDetectionType = dbInterface.getDetectionTypes(self.token)
        self.detectionType_cb.addItems(saDetectionType)

        #saScreenType = dbInterface.getScreenTypes(self.token)
        #self.screenType_cb.addItems(saScreenType)

        self.testDate.setDate(QDate.currentDate())
        
        
    def printPrepLog(self, s, type=''):
        if type == 'error':
            s = f'''<font color='red'>{s}</font>'''
        self.prepLog_te.append(s)
    
    def printQcLog(self, s, type=''):
        if type == 'error':
            s = f'''<font color='red'>{s}</font>'''
        self.qcLog_te.append(s)
        
    def printPlates(self):
        text = self.plates_te.toPlainText()
        lines = text.split('\n')

        # Use a regular expression to filter lines with 'P' followed by 5 digits
        filtered_lines = [line for line in lines if re.match(r'^[pP]\d{5}$', line)]

        # Set the filtered lines back to the QTextEdit
        self.plates_te.setPlainText('\n'.join(filtered_lines))
        iPlates = self.nrOfPlateCopies_sp.value()

        if iPlates == 0:
            return

        plateIndex = [x for x in range(1, iPlates + 1)]
        platesText = self.plates_te.toPlainText()
        saPlates = platesText.split('\n')
        for sPlate in saPlates:
            for i in plateIndex:
                sCurrentPlate = sPlate.upper() + '_' + str(i)
                dbInterface.printPlateLabel(self.token, sCurrentPlate)
                self.printPrepLog(f"Print label {sCurrentPlate}")

        
    def prepareHarmonyFiles(self, file_path):
        data = {
            "plate": [],
            "file": []
        }

        if file_path:
            directory_path = os.path.dirname(file_path)
            try:
                df = pd.read_excel(file_path)
                # Assuming 'plate' and 'file' are column names in the Excel file
                data_dict = df[['plate', 'file']].to_dict(orient='records')
            except Exception as e:
                self.printPrepLog(f"Error reading Excel file: {e}", 'error')
                return
            
            for item in data_dict:
                preparedFile = parseHarmonyFile(self, directory_path, item['file'])
                data['plate'].append(item['plate'])
                data['file'].append(preparedFile)

            sOutFile = os.path.join('/', directory_path, "prepared_plate_to_file.xlsx")
            self.printPrepLog(f'Created {sOutFile}')
            df = pd.DataFrame(data)
            excel_writer = pd.ExcelWriter(sOutFile, engine="openpyxl")
            df.to_excel(excel_writer, sheet_name="Sheet1", index=False)
            excel_writer.close()
            return sOutFile


    def checkForm(self):
        if all(self.form_values.values()):
            self.runQc_btn.setEnabled(True)
        else:
            self.runQc_btn.setDisabled(True)


    def checkDataColumn(self):
        #self.checkForm()
        # Read a csv file from the inputFiles_tab text box and see of the datacolumn in this eb is present
        pass


    def getInputFilesFromTab(self):
        saFiles = []

        for row in range(self.inputFiles_tab.rowCount()):
            item = self.inputFiles_tab.item(row, 0)  # Get item in the first column
            if item is not None:
                saFiles.append(item.text())
        return saFiles


    def updateRawdataStatus(self, sFile, sStatusMessage, sStatusState):

        def color_row(row, sColor = "white"):
            for col in range(self.inputFiles_tab.columnCount()):
                item = self.inputFiles_tab.item(row-1, col)
                if sColor == "red":
                    item.setBackground(QBrush(QColor(255, 0, 0)))  # Set the background color to red
                else:
                    item.setBackground(QBrush(QColor(255, 255, 255)))  # Set the background color to rwhite

        row_position = -1
        for row in range(self.inputFiles_tab.rowCount()):
            # Assuming 'file' is in the first column (index 0)
            item = self.inputFiles_tab.item(row, self.inputFiles_tab.horizontalHeader().logicalIndex(0))
            if item is not None and item.text() == sFile:
                row_position = row

        if row_position == -1:
            self.printQcLog(f'Error can not find {sFile}', 'error')
            return
        
        if sStatusState == 'error':
            color_row(row_position + 1, "red")
        else:
            color_row(row_position + 1, "white")
        item = QTableWidgetItem(sStatusMessage)
        #self.printQcLog(sStatusMessage, sStatusState)
        self.inputFiles_tab.setItem(row_position, 1, item)
        self.inputFiles_tab.resizeColumnsToContents()

        self.inputFiles_tab.scrollToItem(item)
        QApplication.processEvents()

        
    def addFileToTable(self, sFile, full_path):
        row_position = self.inputFiles_tab.rowCount()  # Get the current row count
        self.inputFiles_tab.insertRow(row_position)  # Insert a new row at the end

        fileItem = QTableWidgetItem(sFile)
        statusItem = QTableWidgetItem("Unknown")
        self.inputFiles_tab.setItem(row_position, 0, fileItem)
        self.inputFiles_tab.setItem(row_position, 1, statusItem)
        self.inputFiles_tab.scrollToItem(fileItem)
        self.inputFiles_tab.resizeColumnsToContents()
        QApplication.processEvents()


    def getPlateMapFromDf(self, sPlateId):
        try:
            new_df = self.platemapDf[self.platemapDf['Platt ID'] == sPlateId]
        except:
            self.printQcLog(f'''Can't find plate {sPlateId} in platemap file''', 'error')
            return None
        #new_df = self.platemapDf[self.platemapDf.iloc[:, 0] == sPlateId]
        return new_df


    def extractData(self, sFile, sPlate, saDataLines, iDataColPosition, iWellColPosition):
        columns = ['plate', 'well', 'compound_id', 'batch_id', 'raw_data', 'type']
        df = pd.DataFrame(columns=columns)
        sPosCtrl = self.posCtrl_eb.text()
        sNegCtrl = self.negCtrl_eb.text()
        iSkipped = 0
        iPosCtrl = 0
        iNegCtrl = 0
        iData = 0
        iNoPlatemapEntry = 0

        dfPlatemap = self.getPlateMapFromDf(sPlate)

        for line in saDataLines:
            saLine = line.split(',')
            sType = 'Data'
            selected_row = dfPlatemap[dfPlatemap['Well'] == saLine[iWellColPosition]].copy()
            selected_row = selected_row.reset_index(drop=True)

            try:
                slask = selected_row['Compound ID'][0]
            except:
                iNoPlatemapEntry += 1
                self.printQcLog(f'No platemap for well {saLine[iWellColPosition]} in plate {sPlate}', 'error')
                continue
            try:
                selected_row['Compound ID'][0].startswith('CBK')
            except:
                self.printQcLog(f'''Warning, can't read {saLine[iWellColPosition]} in plate {sPlate}''', 'error')
                continue
            if selected_row['Compound ID'][0] == sPosCtrl:
                sType = 'Pos'
                iPosCtrl += 1
            elif selected_row['Compound ID'][0] == sNegCtrl:
                sType = 'Neg'
                iNegCtrl += 1
            elif selected_row['Compound ID'][0].startswith('CBK'):
                sType = 'Data'
                iData += 1
            else:
                self.printQcLog(f"Skipping well {selected_row['Well'][0]} with compound_id = {selected_row['Compound ID'][0]} in plate {sPlate}", 'error')
                iSkipped += 1
                continue

            try:
                raw_data = saLine[iDataColPosition]
                well = saLine[iWellColPosition]
            except:
                return df
            data = {'plate': sPlate,
                    'well': well,
                    'compound_id': selected_row['Compound ID'][0],
                    'batch_id': selected_row['Batch nr'][0],
                    'raw_data': raw_data,
                    'type': sType}
            df.loc[len(df.index)] = data
        if iData == 0:
            sStatus = 'error'
        else:
            sStatus = 'normal'
        self.updateRawdataStatus(sFile,
                                 f'Data: {iData} PosCtrl: {iPosCtrl} NegCtrl: {iNegCtrl} Skipped: {iSkipped} NoPlateMap: {iNoPlatemapEntry}',
                                 sStatus)
        return df


    def findDataColumns(self, sFileName):
        with open(sFileName, 'r') as sFile:
            saLines = sFile.readlines()
            # Skip all the lines in the start of the file, look for where the 'Well' appears
            for line in saLines:
                saLine = line.split(',')
                if 'Well' in saLine:
                    return saLine

        # This is an error
        return None
        
    
    def digestPlate(self, sPlate, file, sDataColumn):
        saLines = file.readlines()
        iDataColPosition = None
        iWellColPosition = None
        saDataLines = None
        iNrOfCols = 0
        iLineNumber = 0

        # Skip all the lines in the start of the file, look for where the 'Well' appears
        for line in saLines:
            saLine = line.split(',')
            iLineNumber += 1
            if 'Well' in saLine:
                iNrOfCols = len(saLine)
                try:
                    iDataColPosition = saLine.index(sDataColumn)
                except:
                    self.printQcLog(f'Data column {sDataColumn} not present in datafile {file}', 'error')
                    sFile = os.path.basename(file.name)
                    self.updateRawdataStatus(sFile, f"Could not find column {sDataColumn} in file", 'error')
                iWellColPosition = saLine.index('Well')
                saDataLines = saLines[iLineNumber:]
                iLineNumber = 0
                break

        # We did not find any datalines in this file, this is an error state.
        # Here we should pop up a dialog and inform the user.
        if saDataLines == None:
            self.printQcLog(f'No Well found for plate {sPlate}', 'error')
            return saDataLines, iDataColPosition, iWellColPosition

        # Find the last data line and skip all lines below that line.
        for line in saDataLines:
            iLineNumber += 1
            saLine = line.split(',')
            if len(saLine) != iNrOfCols:
                saDataLines = saDataLines[:iLineNumber-1]
            
        return saDataLines, iDataColPosition, iWellColPosition


    def selectFileToPlateMap(self):
        self.inputFiles_tab.setRowCount(0)
        
        file_path, _ = QFileDialog.getOpenFileName(None, "Open File", "", "All Files (*);;Text Files (*.txt)")
        if not file_path:
            return

        path_to_data_dir = os.path.dirname(file_path)

        # If the instrument is Harmony we need to prepare the rawdata files.
        if self.instrument_cb.currentText() == 'Harmony':
            file_path = self.prepareHarmonyFiles(file_path)
        
        self.fileToPlatemapFile = file_path
        df = pd.read_excel(file_path)
        self.fileToPlate_lab.setText(os.path.basename(file_path))
        self.plate_file_dict = df.set_index('plate')['file'].to_dict()
        
        sFiles = ''
        frames = []
        full_path = ''
        for row, (sPlate, sFile) in enumerate(self.plate_file_dict.items()):
            full_path = os.path.join(path_to_data_dir, sFile)
            self.addFileToTable(sFile, full_path)
            self.printQcLog(sFile)
        saDataColumns = self.findDataColumns(full_path)

        if saDataColumns != None:
            self.dataColumn_cb.clear()
            self.dataColumn_cb.addItems(saDataColumns)
            self.generateQcInput_btn.setEnabled(True)
            self.form_values['raw_data_directory'] = True
        else:
            self.printQcLog(f'''Can't find any data lines in file {full_path}''', 'error')


    def selectPlatemap(self):
        options = QFileDialog.Options()
        platemap, _ = QFileDialog.getOpenFileName(
            None, "Open File", "", "All Files (*);;CSV Files (*.csv)", options=options
        )

        if platemap:
            self.platemapDf = pd.read_excel(platemap)
            platemapColumns = self.platemapDf.columns.tolist()
            iCol = 0
            if len(platemapColumns) < 4:
                self.printQcLog('Platemap has wrong format, to few columns', 'error')
                return
            saColOrder = ['Platt ID', 'Well', 'Compound ID', 'Batch nr']
            for sCol in saColOrder:
                if platemapColumns[iCol] != sCol:
                    print(platemapColumns[iCol], sCol)
                    self.printQcLog(f'Platemap has wrong columns, looking for columns in this order {saColOrder}', 'error')
                    return
                iCol += 1
            self.printQcLog(f"Selected file: {platemap}")
            self.platemapFile_lab.setText(os.path.basename(platemap))
            self.form_values['platemap_file'] = True
            self.fileToPlateMap_btn.setEnabled(True)

        self.checkForm()


    def instrumentChange(self):
        sInstrument = self.instrument_cb.currentText()
        saInstrument, iAllOk = dbInterface.getInstrument(self.token, sInstrument)
        if iAllOk:
            #self.dataColumn_cb.setText(saInstrument[0]['data_col'])
            pass


    def generateQcInput(self):
        frames = []
        path_to_data_dir = os.path.dirname(self.fileToPlatemapFile)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        for row, (sPlate, sFile) in enumerate(self.plate_file_dict.items()):
            full_path = os.path.join(path_to_data_dir, sFile)

            with open(full_path, 'r') as file:
                (saDataLines,
                 iDataColPosition,
                 iWellColPosition) = self.digestPlate(sPlate,
                                                      file,
                                                      self.dataColumn_cb.currentText())
                dfPlate = self.extractData(sFile,
                                           sPlate,
                                           saDataLines,
                                           iDataColPosition,
                                           iWellColPosition)
                frames.append(dfPlate)
        resDf = pd.concat(frames)

        def is_numerical(column):
            try:
                pd.to_numeric(column, errors='raise')
                return True
            except (ValueError, TypeError):
                return False

        # Verify 'raw_data' column is numerical
        if 'raw_data' in resDf.columns and is_numerical(resDf['raw_data']):
            pass
        else:
            self.printQcLog(f"The 'raw_data' column is not entirely numerical, did you coose the correct 'Raw data column'?'", 'error')
            QApplication.restoreOverrideCursor()
            return
        
        resDf.to_csv("preparedZinput.csv", sep='\t', index=False)  # Set index=False to exclude the index column
        self.qcInputFile_lab.setText('preparedZinput.csv')
        self.generateQcInput_btn.setEnabled(True)
        QApplication.restoreOverrideCursor()

        self.runQc_btn.setEnabled(True)

        
    def runQc(self):
        self.printQcLog('running QC')
        sOutput = self.outputFile_eb.text()
        iHitThreshold = self.hitThreshold_eb.text()
        try:
            slask = int(iHitThreshold)
        except:
            iHitThreshold = float(-1000.0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        dQcData = calcQc(self, "preparedZinput.csv", sOutput, iHitThreshold)
        QApplication.restoreOverrideCursor()

        if os_name == "Windows":
            subprocess.run(['start', '', sOutput], shell=True, check=True)  # On Windows
        elif os_name == "Darwin":
            subprocess.run(['open', sOutput], check=True)  # On macOS
        elif os_name == "Linux":
            subprocess.run(['xdg-open', sOutput], check=True) # Linux


