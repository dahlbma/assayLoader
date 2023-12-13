import re, sys, os, logging, glob, csv
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QComboBox, QDateEdit
from PyQt5.QtCore import Qt, QDate, QUrl
from PyQt5 import QtGui
from PyQt5.QtGui import QIntValidator, QBrush, QColor
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
        self.prepareHarmony_btn.clicked.connect(self.prepareHarmonyFilesII)
        #self.nrOfPlateCopies_sp           # spin box
        #self.plates_te.                   # text edit
        self.printPlates_btn.clicked.connect(self.printPlates)
        # Prep data screen end
        #####################

        current_directory = os.getcwd()
        self.media_player = QMediaPlayer()
        #self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(f'{current_directory}/beep-07a.wav')))

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
        self.updateGrid_btn.clicked.connect(self.updateGrid)
        self.saveData_btn.clicked.connect(self.saveSpToDb)
        
        self.form_values = {
            "instrument": False,
            "raw_data_column": False,
            "raw_data_directory": False,
            "platemap_file": False,
            "pos_ctrl": False,
            "neg_ctrl": False,
            "qc_output_file": False
        }


    def saveSpToDb(self):
        def color_row_red(row):
            for col in range(self.sp_table.columnCount()):
                item = self.sp_table.item(row, col)
                if item:
                    item.setBackground(QColor('red'))
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        for row in range(self.sp_table.rowCount()):
            row_dict = {}
            for col in range(self.sp_table.columnCount()):
                header_item = self.sp_table.horizontalHeaderItem(col)
                item = self.sp_table.item(row, col)
                if header_item and item:
                    column_name = header_item.text()
                    cell_value = item.text()
                    row_dict[column_name] = cell_value
            
            sRes, lStatus = dbInterface.saveSpRowToDb(self.token, row_dict)
            if lStatus == False:
                color_row_red(row)
            
            QApplication.processEvents()
        QApplication.restoreOverrideCursor()
        
        
    def createPlatemap(self, platesDf, subdirectory_path):
        columns = ['Platt ID', 'Well', 'Compound ID', 'Batch nr', 'Conc (mM)']
        platemapDf = pd.DataFrame(columns=columns)
        
        for index, row in platesDf.iterrows():
            df = pd.DataFrame()
            plate_value = row['plate']
            plate_data, lSuccess = dbInterface.getPlate(self.token, plate_value)
            if lSuccess:
                self.printPrepLog(f'Got plate data for {plate_value}')

                df = pd.DataFrame(plate_data, columns=['Platt ID', 'Well', 'Compound ID', 'Batch nr', 'Conc (mM)'])
            else:
                self.printPrepLog(f'Error getting plate {plate_value} {plate_data}', 'error')
            platemapDf = pd.concat([platemapDf if not platemapDf.empty else None, df], ignore_index=True)

            

        excel_filename = 'PLATEMAP.xlsx'
        full_path = os.path.join(subdirectory_path, excel_filename)
        platemapDf.to_excel(full_path, index=False)

        
    def findColumnNumber(self, sCol):
        iCol = -1
        for col in range(self.sp_table.columnCount()):
            header_item = self.sp_table.horizontalHeaderItem(col)
            header_text = header_item.text()

            if header_text == sCol:
                iCol = col
                break
        return iCol
        
    def populateColumn(self, sCol, sValue):        
        iNrRows = self.sp_table.rowCount()
        iCol = self.findColumnNumber(sCol)

        iRow_index = 0
        for iRow_index in range(iNrRows):
            item = QTableWidgetItem(str(sValue))
            self.sp_table.setItem(iRow_index, iCol, item)


    def save_to_csv(self, filename):
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            
            # Write header
            header = [self.sp_table.horizontalHeaderItem(col).text() for col in range(self.sp_table.columnCount())]
            csvwriter.writerow(header)

            # Write data
            for row in range(self.sp_table.rowCount()):
                row_data = [self.sp_table.item(row, col).text() for col in range(self.sp_table.columnCount())]
                csvwriter.writerow(row_data)


    def updateGrid(self):
        self.populateColumn('project', self.project_cb.currentText())
        self.populateColumn('operator', self.operator_cb.currentText())
        self.populateColumn('target', self.target_cb.currentText())
        self.populateColumn('assay_type', self.assayType_cb.currentText())
        self.populateColumn('detection_type', self.detectionType_cb.currentText())
        testDate = self.testDate.date()
        sDate = testDate.toString("yyyy-MM-dd") 
        self.populateColumn('experiment_date', sDate)
        self.populateColumn('comment', self.comment_eb.text())
        self.populateColumn('eln', self.eln_eb.text())

        self.save_to_csv("gridData.csv")

        
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
        QApplication.processEvents()
    
    def printQcLog(self, s, type='', beep=False):
        if type == 'error':
            s = f'''<font color='red'>{s}</font>'''
            if beep:
                current_directory = os.getcwd()
                self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(f'{current_directory}/beep-07a.wav')))
                self.media_player.play()

        self.qcLog_te.append(s)
        QApplication.processEvents()
        
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

        
    def prepareHarmonyFilesII(self):
        
        def find_files(directory, filename):
            matching_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if file == filename:
                        matching_files.append(os.path.join(root, file))
            return matching_files

        data = {
            "plate": [],
            "file": []
        }

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog  # Use the native file dialog
        directory_dialog = QFileDialog()
        directory_dialog.setOptions(options)
        # Set the file mode to DirectoryOnly to allow selecting directories only
        directory_dialog.setFileMode(QFileDialog.DirectoryOnly)
        # Show the directory dialog
        selected_directory = directory_dialog.getExistingDirectory(self, 'Open Directory', '')

        subdirectory_path = os.path.join(selected_directory, "preparedHaronyFiles")
        try:
            os.makedirs(subdirectory_path)
        except:
            pass

        # Harmony names all raw datafiles to 'PlateResults.txt'
        file_name = 'PlateResults.txt'
        harmony_files = find_files(selected_directory, file_name)

        pattern = re.compile(r'P\d{6}')
        for file_name in harmony_files:
            with open(file_name, 'r') as file:
                content = file.read()
                match = re.search(pattern, content)
                if match:
                    sPlate = match.group()
                    self.printPrepLog(f"Found plate: {sPlate}")
                    preparedFile = parseHarmonyFile(self, subdirectory_path, file_name, sPlate)

                    data['plate'].append(sPlate)
                    data['file'].append(preparedFile)
                else:
                    self.printPrepLog(f"No plate in {file_name}", 'error')

        sOutFile = os.path.join('/', subdirectory_path, "prepared_plate_to_file.xlsx")
        self.printPrepLog(f'Created {sOutFile}')
        df = pd.DataFrame(data)
        df = df.sort_values(by='plate')
        self.createPlatemap(df, subdirectory_path)
        excel_writer = pd.ExcelWriter(sOutFile, engine="openpyxl")
        df.to_excel(excel_writer, sheet_name="Sheet1", index=False)
        excel_writer.close()


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

        return new_df


    def extractData(self, sFile, sPlate, saDataLines, iDataColPosition, iWellColPosition):
        columns = ['plate', 'well', 'compound_id', 'batch_id', 'raw_data', 'type', 'concentration']
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
                well = saLine[iWellColPosition]
                raw_data = float(saLine[iDataColPosition])
            except Exception as e:
                #print(f'{saLine}')
                #print(f'{iDataColPosition}')
                #print(f'{str(e)}')
                self.printQcLog(f'The raw data value is not numeric in plate {sPlate} well {well}', 'error', beep=False)
                #return df
                #raw_data = 0
                continue
            
            data = {'plate': sPlate,
                    'well': well,
                    'compound_id': selected_row['Compound ID'][0],
                    'batch_id': selected_row['Batch nr'][0],
                    'raw_data': raw_data,
                    'type': sType,
                    'concentration': selected_row['Conc (mM)'][0]}
            df.loc[len(df.index)] = data
        if iData == 0 or iPosCtrl == 0 or iNegCtrl == 0:
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
                    #print(sDataColumn)
                    #print(saLine)
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
        file_paht = ''
        if self.instrument_cb.currentText() == 'Harmony':
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog  # Use the native file dialog

            directory_dialog = QFileDialog()
            directory_dialog.setOptions(options)

            # Set the file mode to DirectoryOnly to allow selecting directories only
            directory_dialog.setFileMode(QFileDialog.DirectoryOnly)

            # Show the directory dialog
            file_path = directory_dialog.getExistingDirectory(self, 'Open Directory', '')

        else:
            file_path, _ = QFileDialog.getOpenFileName(None, "Open File", "", "All Files (*);;Text Files (*.txt)")      
 
        if not file_path:
            return

        path_to_data_dir = os.path.dirname(file_path)

        # If the instrument is Harmony we need to prepare the rawdata files.
        if self.instrument_cb.currentText() == 'Harmony':
            file_path = self.prepareHarmonyFilesII(file_path)

            if file_path == "":
                return

        self.fileToPlatemapFile = file_path
        df = pd.read_excel(file_path)

        if df.columns.tolist() != ['plate', 'file'] or len(df.columns) != 2:
            self.printQcLog(f"The file to plate file {file_path} has the wrong format", 'error', beep=True)
            return

        self.fileToPlate_lab.setText(os.path.basename(file_path))
        self.plate_file_dict = df.set_index('plate')['file'].to_dict()
        
        sFiles = ''
        frames = []
        full_path = ''
        for row, (sPlate, sFile) in enumerate(self.plate_file_dict.items()):
            full_path = os.path.join(path_to_data_dir, sFile)
            self.addFileToTable(sFile, full_path)

            if os.path.exists(full_path):
                self.printQcLog(f"{sFile} exists")
            else:
                self.printQcLog(f"{sFile} does not exist.", 'error', beep=True)

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

            try:
                with open(full_path, 'r') as file:
                    (saDataLines,
                     iDataColPosition,
                     iWellColPosition) = self.digestPlate(sPlate,
                                                          file,
                                                          self.dataColumn_cb.currentText())
                    try:
                        iDataColPosition = int(iDataColPosition)
                    except:
                        print(f'iDataColPosition ', iDataColPosition)
                        continue
                    
                    dfPlate = self.extractData(sFile,
                                               sPlate,
                                               saDataLines,
                                               iDataColPosition,
                                               iWellColPosition)
                    frames.append(dfPlate)
            except Exception as e:
                print(str(e))
                self.printQcLog(f"Can't open {full_path}", 'error', beep=True)
                QApplication.restoreOverrideCursor()
                return
        resDf = pd.concat(frames)

        def is_numerical(column):
            try:
                pd.to_numeric(column, errors='raise')
                return True
            except (ValueError, TypeError):
                return False
        
        mean_value = resDf['raw_data'].mean()
        median_value = resDf['raw_data'].median()
        std_deviation = resDf['raw_data'].std()
        
        if 'raw_data' in resDf.columns and is_numerical(resDf['raw_data']) and std_deviation != 0.0:
            pass
        else:
            self.printQcLog(f"Can't do statistics on 'raw_data', did you choose the correct 'Raw data column'?'",
                            'error',
                            beep=True)
            QApplication.restoreOverrideCursor()
            return
        
        resDf.to_csv("preparedZinput.csv", sep='\t', index=False)  # Set index=False to exclude the index column
        self.qcInputFile_lab.setText('preparedZinput.csv')
        self.generateQcInput_btn.setEnabled(True)
        QApplication.restoreOverrideCursor()

        self.runQc_btn.setEnabled(True)


    def populate_table(self, dataframe, column_name, insertRows=False):

        def insertRow(iNrOfRows, iNrOfCols):
            iLocalCol = 0
            for iRow in range(iNrOfRows):
                self.sp_table.insertRow(iRow)
                for iCol in range(iNrOfCols):
                    item = QTableWidgetItem(str(''))
                    self.sp_table.setItem(iRow, iCol, item)

        if insertRows:
            insertRow(dataframe.shape[0], self.sp_table.columnCount())

        iCol = self.findColumnNumber(column_name)

        if iCol == -1:
            self.printQcLog(f"Couldn't find column {column_name}", 'error')
            return
        
        # Populate the specified column of the table with data from the DataFrame
        iRow_index = 0
        for row_index, row_data in dataframe.iterrows():
            item = QTableWidgetItem(str(row_data[column_name]))

            self.sp_table.setItem(iRow_index, iCol, item)
            iRow_index += 1

        
    def runQc(self):
        self.printQcLog('running QC')
        sOutput = self.outputFile_eb.text()
        iHitThreshold = self.hitThreshold_eb.text()
        try:
            slask = int(iHitThreshold)
        except:
            iHitThreshold = float(-1000.0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            newHitThreshold, dfQcData = calcQc(self, "preparedZinput.csv", sOutput, iHitThreshold)
        except Exception as e:
            print(f"{str(e)}")
            self.printQcLog(f"Error calculating QC", 'error')
            QApplication.restoreOverrideCursor()
            return

        dfQcData['inhibition'] = pd.to_numeric(dfQcData['inhibition'], errors='coerce').round(2)
        newHitThreshold = "{:.2f}".format(newHitThreshold)
        self.hitThreshold_eb.setText(str(newHitThreshold))

        mask = dfQcData['compound_id'].str.startswith('CBK')
        dfQcData = dfQcData[mask].reset_index(drop=True)
        

        if os_name == "Windows":
            subprocess.run(['start', '', sOutput], shell=True, check=True)  # On Windows
        elif os_name == "Darwin":
            subprocess.run(['open', sOutput], check=True)  # On macOS
        elif os_name == "Linux":
            subprocess.run(['xdg-open', sOutput], check=True) # Linux

        self.sp_table.setRowCount(0)
        self.populate_table(dfQcData, 'compound_id', insertRows=True)
        self.populate_table(dfQcData, 'batch_id')
        self.populate_table(dfQcData, 'inhibition')
        self.populate_table(dfQcData, 'hit')
        self.populate_table(dfQcData, 'plate')
        self.populate_table(dfQcData, 'well')
        self.populate_table(dfQcData, 'concentration')

        self.populateColumn('hit_threshold', newHitThreshold)

        QApplication.restoreOverrideCursor()
