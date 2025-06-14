import re, os, logging, csv
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QComboBox
from PyQt5.QtCore import Qt, QDate, QUrl, QRegExp
from PyQt5.QtGui import QBrush, QColor, QDoubleValidator, QRegExpValidator
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import pandas as pd
import subprocess
from z_factor import *
from assaylib import *
from prepareHarmonyFile import *
from prepareEnvisionFile import *
import platform
from inhibitionScatter import ScatterPlotWindow

# Get the operating system name
os_name = platform.system()

class SinglePointScreen(QMainWindow):
    from assaylib import gotoDR
    def __init__(self, token, test):
        super(SinglePointScreen, self).__init__()
        self.test = test
        self.token = token
        self.mod_name = "loader"
        self.logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/singlePointTab.ui"), self)

        self.rVolume = None
        self.finalVolume_eb.textChanged.connect(self.wellVolumeChanged)
        regex = QRegExp("[0-9]+.?[0-9]*")  # Only digits 1-9 and a single dot
        validator = QRegExpValidator(regex, self.finalVolume_eb)
        self.finalVolume_eb.setValidator(validator)
        
        self.preparedZinput = 'preparedZinput.csv'
        self.QCoutput = 'screenQC.xlsx'
        self.workingDirectory = ''
        
        #####################
        # Prep data screen
        self.prepareHarmony_btn.clicked.connect(self.prepareHarmonyFiles)
        self.envision_plateID_to_file_btn.clicked.connect(self.prepareEnvisionFiles)
        self.printPlates_btn.clicked.connect(self.printPlates)
        self.prepareHarmony_btn.setEnabled(False)
        self.envision_plateID_to_file_btn.setEnabled(False)
        # Prep data screen end
        #####################

        current_directory = os.getcwd()
        self.media_player = QMediaPlayer()
        #self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(f'{current_directory}/beep-07a.wav')))

        self.goto_dr_btn.clicked.connect(self.gotoDR)

        self.dataColumn_cb.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        saInstruments = dbInterface.getInstruments(self.token)
        saInstruments = [""] + saInstruments
        self.instrument_cb.addItems(saInstruments)
        self.instrument_cb.currentIndexChanged.connect(self.instrumentChange)
        
        #self.dataColumn_cb.editingFinished.connect(self.checkDataColumn)
        self.fileToPlateMap_btn.clicked.connect(self.selectFileToPlateMap)
        self.fileToPlateMap_btn.setDisabled(True)
        
        self.runQc_btn.setEnabled(True)
        #self.runQc_btn.setDisabled(True)
        self.runQc_btn.clicked.connect(self.runQc)

        self.generateQcInput_btn.setDisabled(True)
        self.generateQcInput_btn.clicked.connect(self.generateQcInput)

        self.outputFile_eb.editingFinished.connect(self.checkDataColumn)
        self.outputFile_eb.setText(self.QCoutput)

        self.posCtrl_eb.editingFinished.connect(self.checkDataColumn)
        self.posCtrl_eb.setText('CTRL')

        self.negCtrl_eb.editingFinished.connect(self.checkDataColumn)
        self.negCtrl_eb.setText('DMSO')

        double_validator = QDoubleValidator()
        double_validator.setLocale(double_validator.locale().c())  
        
        self.hitThreshold_eb.setValidator(double_validator)
        
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
        self.loadAssayFile_btn.clicked.connect(self.loadAssayDataFromFile)
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

        validator = QDoubleValidator()
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.minPosCtrl_eb.setValidator(validator)
        self.maxNegCtrl_eb.setValidator(validator)


    def wellVolumeChanged(self, sVolume):
        try:
            self.rVolume = float(sVolume)
        except:
            self.prepareHarmony_btn.setEnabled(False)
            self.rVolume = None
            return
        
        self.prepareHarmony_btn.setEnabled(True)
        self.envision_plateID_to_file_btn.setEnabled(True)
 
 
    def saveSpToDb(self):

        def getDateColumn():
            column_count = self.sp_table.columnCount()
            # Initialize an empty list to store column names
            column_names = []

            # Loop through each column index
            for col in range(column_count):
                # Get the horizontal header item for the column
                header_item = self.sp_table.horizontalHeaderItem(col)
    
                # Check if the header item is not None
                if header_item.text() == 'experiment_date':
                    return col
        iDateCol = getDateColumn()
        item = self.sp_table.item(0, iDateCol)
        
        if self.sp_table.rowCount() > 0 and item is not None and item.text().strip() == "":
            self.updateGrid()
        
        def repopulate_errors(df):
            self.populate_table(df, 'compound_id', insertRows=True, error=True)
            self.populate_table(df, 'batch_id', error=True)
            self.populate_table(df, 'target', error=True)
            self.populate_table(df, 'model_system', error=True)
            self.populate_table(df, 'project', error=True)
            self.populate_table(df, 'plate', error=True)
            self.populate_table(df, 'well', error=True)
            self.populate_table(df, 'assay_type', error=True)
            self.populate_table(df, 'detection_type', error=True)
            self.populate_table(df, 'viability_measurement', error=True)
            self.populate_table(df, 'concentration', error=True)
            self.populate_table(df, 'inhibition', error=True)
            self.populate_table(df, 'activation', error=True)
            self.populate_table(df, 'hit', error=True)
            self.populate_table(df, 'hit_threshold', error=True)
            self.populate_table(df, 'test_date', error=True)
            self.populate_table(df, 'operator', error=True)
            self.populate_table(df, 'eln', error=True)
            self.populate_table(df, 'comment', error=True)

        repopulate_data = []
        def uploadRows(rows, targetTable):
            if accumulated_rows == []:
                return

            sRes, lStatus = dbInterface.saveSpRowToDb(self.token, accumulated_rows, targetTable)
            
            if lStatus == False:
                for ro in sRes:
                    repopulate_data.append(ro)

        accumulated_rows = []
        iAccumulator_count = 0
        iRowsBatch = 8
        targetTable = self.targetTable_cb.currentText()
        self.popup = PopUpProgress(f'Uploading data')
        self.popup.show()
        iNrOfRows = self.sp_table.rowCount()
        iTick = 0
        rProgressSteps = (iRowsBatch/iNrOfRows)*100

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
            accumulated_rows.append(row_dict)
            iAccumulator_count += 1

            if iAccumulator_count == iRowsBatch:
                uploadRows(accumulated_rows, targetTable)
                accumulated_rows = []
                iAccumulator_count = 0
            
                iTick += rProgressSteps
                self.popup.obj.proc_counter(int(iTick))
                QApplication.processEvents()

        if iAccumulator_count > 0:
            uploadRows(accumulated_rows, targetTable)

        self.sp_table.setRowCount(0)
        dfRepopulate = pd.DataFrame(repopulate_data)
        repopulate_errors(dfRepopulate)
        QApplication.restoreOverrideCursor()
        self.popup.obj.proc_counter(100)
        self.popup.close()

        
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
        # Open the CSV file for writing
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='\t')

            # Write the header row
            header = [self.sp_table.horizontalHeaderItem(col).text() for col in range(self.sp_table.columnCount())]
            writer.writerow(header)

            # Write each row of data
            for row in range(self.sp_table.rowCount()):
                row_data = []
                for col in range(self.sp_table.columnCount()):
                    item = self.sp_table.item(row, col)
                    row_data.append(item.text() if item else "")
                writer.writerow(row_data)


    def loadAssayDataFromFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        loadAssayDataDialog = QFileDialog()
        loadAssayDataDialog.setOptions(options)

        fileName, _ = loadAssayDataDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv *.CSV)")

        if not fileName:
            return

        num_columns = self.sp_table.columnCount()
        
        # Read CSV file
        with open(fileName, 'r') as file:
            reader = csv.reader(file, delimiter='\t')
            header = next(reader)  # Skip the header row
            data = list(reader)

        num_columns = self.sp_table.columnCount()
        try:
            iCsvColumnCount = len(data[0])
            if iCsvColumnCount == 1:
                with open(fileName, 'r') as file:
                    reader = csv.reader(file, delimiter=',')
                    header = next(reader)  # Skip the header row
                    data = list(reader)
                    iCsvColumnCount = len(data[0])
        except:
            print('CSV file has no data')
            return
        
        if num_columns != iCsvColumnCount:
            print(f'CSV file has wrong number of columns looking for {num_columns} columns but got {iCsvColumnCount}')
            return
        
        # Set table dimensions
        self.sp_table.setRowCount(len(data))
        self.sp_table.setColumnCount(len(data[0]))

        # Populate table with data
        for row in range(len(data)):
            for col in range(len(data[0])):
                item = QTableWidgetItem(data[row][col])
                self.sp_table.setItem(row, col, item)


    def updateGrid(self):
        self.populateColumn('project', self.project_cb.currentText())
        self.populateColumn('operator', self.operator_cb.currentText())
        self.populateColumn('target', self.target_cb.currentText())
        self.populateColumn('model_system', self.screenType_cb.currentText())
        self.populateColumn('assay_type', self.assayType_cb.currentText())
        self.populateColumn('detection_type', self.detectionType_cb.currentText())
        self.populateColumn('viability_measurement', self.viabilityMeasure_cb.currentText())
        testDate = self.testDate.date()
        sDate = testDate.toString("yyyy-MM-dd") 
        self.populateColumn('experiment_date', sDate)
        self.populateColumn('comment', self.comment_eb.text())
        self.populateColumn('eln', self.eln_eb.text())

        sOutput = os.path.join(self.workingDirectory, "gridData.csv")
        self.save_to_csv(sOutput)


    def populateScreenData(self):
        saProjects = dbInterface.getProjects(self.token)
        self.project_cb.addItems(saProjects)

        saOperators = dbInterface.getOperators(self.token)
        self.operator_cb.addItems(saOperators)

        saTargets = dbInterface.getTargets(self.token)
        self.target_cb.addItems(saTargets)

        saModelTypes = [
            'Cell_Line',
            'Protein',
            'Primary_Cell',
            'Organism',
            'IPSC',
            'Tissue',
            'Virus',
            'other'
            ]
        self.screenType_cb.addItems(saModelTypes)

        saAssayTypes = [
            "Phenotypic_2D",
            "Phenotypic_Suspension",
            "Phenotypic_3D",
            "Targeted_Cell-based_2D",
            "Targeted_Cell-based_Suspension",
            "Targeted_Cell-based_3D",
            "Protein_Binding",
            "Protein_Enzymatic"
        ]
        #saAssayTypes = dbInterface.getAssayTypes(self.token)
        self.assayType_cb.addItems(saAssayTypes)

        saTargetTables = [
            "Sandbox table",
            "Primary screen",
            "Confirmation screen",
            "Counter screen"
        ]
        self.targetTable_cb.addItems(saTargetTables)
        
        saViabilityMeasurement = [
            'Imaging',
            'Luminescence',
            'Other',
            'No'
        ]
        saViabilityMeasurement = [
            'Yes',
            'No'
        ]

        saDetectionType = [
            'Imaging',
            'Luminescence',
            'Other',
            'No'
        ]
        
        self.detectionType_cb.addItems(saDetectionType)
        self.viabilityMeasure_cb.addItems(saViabilityMeasurement)

        
        #saScreenType = dbInterface.getScreenTypes(self.token)
        #self.screenType_cb.addItems(saScreenType)

        self.testDate.setDate(QDate.currentDate())
        
    
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


    def prepareEnvisionFiles(self):
        subdirectory_path = ''
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        envision_dialog = QFileDialog()
        envision_dialog.setOptions(options)

        fileName, _ = envision_dialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        if fileName:
            subdirectory_path = os.path.dirname(fileName)
        prepared_path = os.path.join(subdirectory_path, "assayLoaderEnvisionFiles")
        delete_all_files_in_directory(prepared_path)
        self.workingDirectory = prepared_path
        if prepared_path == "assayLoaderEnvisionFiles":
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            sPlatemapFile, fullFileName = findEnvisionFiles(self, prepared_path, fileName)
        except:
            QApplication.restoreOverrideCursor()
            return
        self.selectPlatemap(sPlatemapFile)
        self.selectFileToPlateMap(fullFileName)
        self.instrument_cb.setCurrentText('Envision')
        QApplication.restoreOverrideCursor()


    def prepareHarmonyFiles(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog  # Use the native file dialog
        directory_dialog = QFileDialog()
        directory_dialog.setOptions(options)
        # Set the file mode to DirectoryOnly to allow selecting directories only
        directory_dialog.setFileMode(QFileDialog.DirectoryOnly)
        # Show the directory dialog
        selected_directory = directory_dialog.getExistingDirectory(self, 'Open Directory', '')
        subdirectory_path = os.path.join(selected_directory, "assayLoaderHarmonyFiles")
        self.workingDirectory = subdirectory_path
        if subdirectory_path == "assayLoaderHarmonyFiles":
            return

        delete_all_files_in_directory(subdirectory_path)
        sPlatemapFile, plateIdToFileMapping = findHarmonyFiles(self, subdirectory_path, selected_directory)
        self.instrument_cb.setCurrentText('Harmony')
        self.selectFileToPlateMap(plateIdToFileMapping)
        self.selectPlatemap(sPlatemapFile)
        

    def checkForm(self):
        if all(self.form_values.values()):
            self.runQc_btn.setEnabled(True)
        else:
            self.runQc_btn.setDisabled(True)


    def checkDataColumn(self):
        #self.checkForm()
        # Read a csv file from the inputFiles_tab text box and see of the datacolumn in this eb is present
        pass


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
                self.printQcLog(f'The raw data value is not numeric in plate {sPlate} well {well}', 'error', beep=False)
                continue


            currentConc = selected_row['Conc mM'][0]
            currentVolume = selected_row['volume nL'][0]
            targetVolume = self.rVolume

            if currentVolume != targetVolume:
                targetConc = (currentConc * currentVolume) / targetVolume
            else:
                targetConc = selected_row['Conc mM'][0]
            data = {'plate': sPlate,
                    'well': well,
                    'compound_id': selected_row['Compound ID'][0],
                    'batch_id': selected_row['Batch nr'][0],
                    'raw_data': raw_data,
                    'type': sType,
                    'concentration': targetConc,
                    'volume': targetVolume}
            df.loc[len(df.index)] = data
        if iData == 0 or iPosCtrl == 0 or iNegCtrl == 0:
            sStatus = 'error'
        else:
            sStatus = 'normal'
        self.updateRawdataStatus(sFile,
                                 f'Data: {iData} PosCtrl: {iPosCtrl} NegCtrl: {iNegCtrl} Skipped: {iSkipped} NoPlateMap: {iNoPlatemapEntry}',
                                 sStatus)
        return df

    
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


    def selectFileToPlateMap(self, file_path = False):
        self.inputFiles_tab.setRowCount(0)

        if file_path == False:
            file_paht = ''
            file_path, _ = QFileDialog.getOpenFileName(None, "Open File", "", "All Files (*);;Text Files (*.txt)")      
 
        if not file_path:
            return

        path_to_data_dir = os.path.dirname(file_path)
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

        saDataColumns = assaylib.findDataColumns(full_path)

        if saDataColumns != None:
            self.dataColumn_cb.clear()
            self.dataColumn_cb.addItems(saDataColumns)
            self.generateQcInput_btn.setEnabled(True)
            self.form_values['raw_data_directory'] = True
        else:
            self.printQcLog(f'''Can't find any data lines in file {full_path}''', 'error')


    def selectPlatemap(self, platemap = False):
        if platemap == False:
            platemap, _ = QFileDialog.getOpenFileName(self, "Open File", self.workingDirectory)

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
                        continue
                    dfPlate = self.extractData(sFile,
                                               sPlate,
                                               saDataLines,
                                               iDataColPosition,
                                               iWellColPosition)
                    frames.append(dfPlate)
            except Exception as e:
                self.printQcLog(f"Can't open {full_path} str(e)", 'error', beep=True)
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
        sOutput = os.path.join(self.workingDirectory, self.preparedZinput)
        resDf.to_csv(sOutput, sep='\t', index=False)  # Set index=False to exclude the index column
        self.qcInputFile_lab.setText(sOutput)
        self.generateQcInput_btn.setEnabled(True)
        QApplication.restoreOverrideCursor()

        self.runQc_btn.setEnabled(True)


    def populate_table(self, dataframe, column_name, insertRows=False, error=False):
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
            if error == True:
                item.setBackground(QBrush(QColor('red')))
            iRow_index += 1


    def show_scatter_plot(self, df, iHitLimit):
        scatter_window = ScatterPlotWindow(self)
        scatter_window.setGeometry(200, 200, 800, 600)
        scatter_window.show_data(df, iHitLimit)
        scatter_window.show()


    def inhibitionScatterPlot(self, df_inhibition, hitLimit):
        # Create a scatterplot of the "inhibition" columns
        plt.scatter(range(len(df_inhibition)), df_inhibition['posCtrlInhibition'], label='PosCtrl', marker='.', s=1, c='green')
        plt.scatter(range(len(df_inhibition)), df_inhibition['inhibition'], label='Inhibition', marker='.', s=2, c='blue')
        plt.scatter(range(len(df_inhibition)), df_inhibition['negCtrlInhibition'], label='NegCtrl', marker='.', s=1, c='red')
        # Draw a horizontal line at the hit limit
        plt.axhline(y=hitLimit, color='red', linestyle='--', label='Hit Limit')
        
        # Set labels and title
        plt.xlabel('Data Points')
        plt.ylabel('Inhibition')
        plt.title('Inhibition scatterplot')
        
        # Add a legend
        plt.legend()
        
        image_buffer = io.BytesIO()
        plt.savefig(image_buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        return image_buffer

        
    def runQc(self):
        self.printQcLog('running QC')
        sOutput = os.path.join(self.workingDirectory, self.outputFile_eb.text())
        self.QCoutput = sOutput
        iMinPosCtrl = int(self.minPosCtrl_eb.text())
        iMaxNegCtrl = int(self.maxNegCtrl_eb.text())

        iHitThreshold = self.hitThreshold_eb.text()
        try:
            slask = float(iHitThreshold)
        except:
            iHitThreshold = float(-1000.0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            newHitThreshold, dfQcData = calcQc(self,
                                               os.path.join(self.workingDirectory, self.preparedZinput),
                                               self.QCoutput,
                                               iHitThreshold,
                                               iMinPosCtrl,
                                               iMaxNegCtrl)
        except Exception as e:
            self.printQcLog(f"Error calculating QC {str(e)}", 'error')
            QApplication.restoreOverrideCursor()
            return
        
        self.show_scatter_plot(dfQcData, newHitThreshold)
        
        dfQcData['inhibition'] = pd.to_numeric(dfQcData['inhibition'], errors='coerce').round(2)
        newHitThreshold = "{:.2f}".format(newHitThreshold)
        self.hitThreshold_eb.setText(str(newHitThreshold))

        mask = dfQcData['compound_id'].str.startswith('CBK')
        dfQcData = dfQcData[mask].reset_index(drop=True)

        if os_name == "Windows":
            subprocess.run(['start', '', self.QCoutput], shell=True, check=True)  # On Windows
        elif os_name == "Darwin":
            subprocess.run(['open', self.QCoutput], check=True)  # On macOS
        elif os_name == "Linux":
            subprocess.run(['xdg-open', self.QCoutput], check=True) # Linux

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
