import re, sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import openpyxl
import csv
from pathlib import Path
import xlsxwriter

from assaylib import *

class SinglePointScreen(QMainWindow):
    from assaylib import gotoDR, gotoSP
    def __init__(self, token, test):
        super(SinglePointScreen, self).__init__()
        self.token = token
        self.mod_name = "loader"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/singlePointTab.ui"), self)
        
        
        self.goto_sp_btn.clicked.connect(self.gotoSP)
        self.goto_dr_btn.clicked.connect(self.gotoDR)

        self.spPlateIdFile_btn.clicked.connect(self.loadPlates)
        self.rawDataFiles_btn.clicked.connect(self.loadRawData)
        header = self.rawDataFiles_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)


        self.spGenerateBreezeInput_btn.clicked.connect(self.createBreezeFile)
        
        self.testDate.setCalendarPopup(True)
        self.testDate.setDateTime(QtCore.QDateTime.currentDateTime())
        
        projects = dbInterface.getProjects(self.token)
        self.project_cb.addItems(projects)

        targets = dbInterface.getTargets(self.token)
        self.target_cb.addItems(targets)

        assayTypes = dbInterface.getAssayTypes(self.token)
        self.assay_type_cb.addItems(assayTypes)

        detectionTypes = dbInterface.getDetectionTypes(self.token)
        self.det_type_cb.addItems(detectionTypes)
        
        operators = dbInterface.getOperators(self.token)
        self.operator_cb.addItems(operators)

        self.screenType_cb.addItems(['Activation', 'Inhibition'])

        self.loadAssayFile_btn.clicked.connect(self.loadAssayFile)

        self.saveData_btn.setEnabled(False)
        
        try:
            js = dbInterface.getSinglePointConfig(self.token)
            self.spConfig = json.loads(js)
            sp_header = [str(h) for h in self.spConfig]
            sp_header.append('Error')
            iIndex = 0
            for h in self.spConfig:
                colData = self.spConfig[h]
                if colData['verify_id']:
                    self.spVerifyColInfo = {"verifyCol": iIndex,
                                            "verifyDbCol": colData['verify_name']}
                iIndex += 1
            js = dbInterface.getDoseResponseConfig(self.token)
            self.drConfig = json.loads(js)
            dr_header = [str(h) for h in self.drConfig]
        except Exception as e:
            print(str(e))

        self.sp_table.setColumnCount(len(sp_header))
        self.sp_table.setHorizontalHeaderLabels(sp_header)

    def loadAssayFile(self):
        fname = QFileDialog.getOpenFileName(self, 'Import Assay Data', 
                                            '.', "")
        if fname[0] == '':
            return
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        workBook = openpyxl.load_workbook(fname[0], read_only=True)
        workSheet = workBook[workBook.sheetnames[0]]

        workSheet.reset_dimensions()
        workSheet.calculate_dimension(force=True)

        iRow = 0
        saSheetHeader = []
        for row in workSheet.rows:
            if iRow == 0:
                for cell in row:
                    saSheetHeader.append(cell.value)
            break

        if self.verifyXlHeader(self.spConfig, saSheetHeader) == True:
            self.populateAssayTable(workSheet)
        QApplication.restoreOverrideCursor()


    def verifyXlHeader(self, confHeader, xlHeader):
        iCount = 0
        lAllOK = True
        for item in confHeader:
            if item == xlHeader[iCount]:
                pass
            else:
                lAllOK = False
                print(f'Column error: Expected column name "{item}" in position \
                {iCount +1}, but got "{xlHeader[iCount]}"')
            
            iCount += 1
        return lAllOK


    def populateAssayTable(self, workSheet):
        saCompIds = dbInterface.getBatchCompound(self.token,
                                                 self.spVerifyColInfo['verifyDbCol'])
        errorColor = QtGui.QColor(255, 0, 0)
        iRow = 0
        for row in workSheet.values:
            if iRow == 0: # Skip header row
                iRow +=1
                continue
            iRow += 1
            rowPosition = self.sp_table.rowCount()
            self.sp_table.insertRow(rowPosition)
            iCol = 0
            lError = False
            for value in row:
                self.sp_table.setItem(rowPosition, iCol, QTableWidgetItem(str(value)))
                if iCol == self.spVerifyColInfo['verifyCol'] and value not in ('POS', 'DMSO', 'empty'):
                    if iCol == self.spVerifyColInfo['verifyCol'] and value not in saCompIds:
                        self.sp_table.item(rowPosition, self.spVerifyColInfo['verifyCol']).setBackground(errorColor)
                        lError = True
                iCol += 1
                
            if lError:
                self.sp_table.setItem(rowPosition, iCol, QTableWidgetItem(str(1)))
            else:
                self.sp_table.setItem(rowPosition, iCol, QTableWidgetItem(str(0)))

        self.sp_table.setSortingEnabled(True)
        
    def loadPlates(self):
        fname = QFileDialog.getOpenFileName(self, 'Import plates', '.', "")
        if fname[0] == '':
            return
        self.spPlateFile_lab.setText(fname[0])
        
    def loadRawData(self):
        filter = "TXT (*.txt);;PDF (*)"
        file_name = QFileDialog()
        file_name.setFileMode(QFileDialog.ExistingFiles)
        names = file_name.getOpenFileNames(self, 'Import plates', '.', "")
        if names[0] == '':
            return
        sFiles = ""

        self.rawDataFiles_table.setRowCount(0)
        self.rawDataFiles_table.setRowCount(len(names[0]))
        
        iRow = 0
        iCol = 0
        self.saFiles = []
        for file in names[0]:
            self.saFiles.append(file)
            newItem = QTableWidgetItem(str(file))
            self.rawDataFiles_table.setItem(iRow, iCol, newItem)
            self.rawDataFiles_table.setRowHeight(iRow, 12)
            iRow += 1

    def createBreezeFile(self):
        workBook = openpyxl.load_workbook(self.spPlateFile_lab.text(), read_only=True)
        workSheet = workBook[workBook.sheetnames[0]]

        workSheet.reset_dimensions()
        workSheet.calculate_dimension(force=True)

        sPlateIdColName = workSheet["B1"].value
        sPlateFilenameColName = workSheet["C1"].value

        if sPlateIdColName != 'Platt ID' or sPlateFilenameColName != 'Filename':
            send_msg(f'Wrong header in file',
                     f'Column B1 must be named "Platt ID" and C1 "Filename"\nGot: B1 "{sPlateIdColName}" and C1 "{sPlateFilenameColName}"')
            return

        iRow = 0
        saSheetHeader = []
        resultList = list()

        for row in workSheet.rows:
            iCol = 0
            if iRow == 0: # Skip header row
                iRow += 1
                continue
            iRow += 1
            sPlateId = ""
            sRawDataFilename = ""
            for cell in row:
                if iCol == 1:
                    sPlateId = str(cell.value)
                if iCol == 2:
                    sRawDataFilename = str(cell.value)
                if iCol == 2:
                    sFullRawDataFilePath = self.checkIfFileExists(sRawDataFilename)
                    if not sFullRawDataFilePath:
                        send_msg('Raw data file not found',
                                 f'Could not find the rawdata file "{sRawDataFilename}"')
                        return
                    else:
                        res = self.parseRawDataAndPlate(sFullRawDataFilePath, sPlateId, iRow-2)
                        if res:
                            resultList.append(res)

                iCol += 1
        #resultList = resultList[0]
        resultList = [item for subList in resultList for item in subList]
        filename, _ = QFileDialog.getSaveFileName()
        
        if not filename.endswith('.txt'):
            filename = filename + '.txt'
        if filename == '.csv':
            return
            
        if filename:
            saHeader = ['WELL', 'WELL_SIGNAL', 'SCREEN_NAME', 'PLATE', 'DRUG_NAME', 'CONCENTRATION']
            with open(filename, 'w', encoding='UTF8', newline='\n') as f:
                #writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_NONE)
                writer = csv.writer(f, dialect='unix', quoting=csv.QUOTE_NONE, delimiter='\t')
                # write the header
                writer.writerow(saHeader)
                # write multiple rows
                writer.writerows(resultList)
            f.close()
                
        
    def checkIfFileExists(self, sRawDataFilename):
        for sFile in self.saFiles:
            if sRawDataFilename in sFile:
                return sFile
        return False
            
    def parseRawDataAndPlate(self, sFullRawDataFilePath, sPlateId, iTableRow):
        saPlate, bStatus = dbInterface.getPlate(self.token, sPlateId)
        if bStatus == False:
            errorColor = QtGui.QColor(255, 0, 0)
            newItem = QTableWidgetItem(str(saPlate))
            self.rawDataFiles_table.setItem(iTableRow, 1, newItem)
            self.rawDataFiles_table.item(iTableRow, 1).setBackground(errorColor)
            return False
        else:
            jsonPlate = json.loads(saPlate)
            newItem = QTableWidgetItem(f'Loaded {len(jsonPlate)} wells from plate {sPlateId}')
            self.rawDataFiles_table.setItem(iTableRow, 1, newItem)
            okColor = QtGui.QColor(0, 255, 0)
            self.rawDataFiles_table.item(iTableRow, 1).setBackground(okColor)
            
            f = open(sFullRawDataFilePath, "r")
            bDataFound = False
            sScreenName = self.screenName_eb.text()
            saResult = list()
            
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.strip()
                saRawColumns = line.split(',')
                if bDataFound and len(saRawColumns) == 1:  # This is true when all assay lines are read
                    break
                if saRawColumns[0] == 'PlateNumber': # This is the header line for assay lines
                    bDataFound = True
                    continue
                if bDataFound:
                    for row in jsonPlate:
                        if row['WELL'] == saRawColumns[4]: # Find the plate info for the current well in the raw data file
                            saResult.append(list((row['WELL'], saRawColumns[14], sScreenName, row['PLATE'], row['DRUG_NAME'], row['CONCENTRATION'])))
            return saResult
        # jsonPlate entry looks like:
        #{
        #        "PLATE": "P014544",
        #        "WELL": "P13",
        #        "DRUG_NAME": "AA3081722",
        #        "CONCENTRATION": 10.0
        #}
        
        # The two columns in the raw datafile that we need are:
        # well   = col 5
        # result = col 15
        
        # Output file should have these columns
        # WELL  WELL_SIGNAL SCREEN_NAME PLATE   DRUG_NAME CONCENTRATION
        # A1    64240       Holmgren    P014569 CBK062263 10

