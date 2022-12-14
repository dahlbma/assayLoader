import re, sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import openpyxl
from assaylib import *

class DoseResponseScreen(QMainWindow):
    from assaylib import gotoDR, gotoSP
    def __init__(self, token, test):
        super(DoseResponseScreen, self).__init__()
        self.token = token
        self.mod_name = "loader"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/doseResponseTab.ui"), self)
        
        
        self.goto_sp_btn.clicked.connect(self.gotoSP)
        self.goto_dr_btn.clicked.connect(self.gotoDR)
        
        self.testDate_dr.setCalendarPopup(True)
        self.testDate_dr.setDateTime(QtCore.QDateTime.currentDateTime())
        
        projects = dbInterface.getProjects(self.token)
        self.projectDr_cb.addItems(projects)

        targets = dbInterface.getTargets(self.token)
        self.targetDr_cb.addItems(targets)

        assayTypes = dbInterface.getAssayTypes(self.token)
        self.assay_typeDr_cb.addItems(assayTypes)

        detectionTypes = dbInterface.getDetectionTypes(self.token)
        self.det_typeDr_cb.addItems(detectionTypes)
        
        operators = dbInterface.getOperators(self.token)
        self.operatorDr_cb.addItems(operators)

        self.loadAssayFileDr_btn.clicked.connect(self.loadAssayFile)

        self.saveDataDr_btn.setEnabled(False)
        
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

        self.dr_table.setColumnCount(len(dr_header))
        self.dr_table.setHorizontalHeaderLabels(dr_header)


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
            rowPosition = self.dr_table.rowCount()
            self.dr_table.insertRow(rowPosition)
            iCol = 0
            lError = False
            for value in row:
                self.dr_table.setItem(rowPosition, iCol, QTableWidgetItem(str(value)))
                if iCol == self.spVerifyColInfo['verifyCol'] and value not in saCompIds:
                    self.dr_table.item(rowPosition, self.spVerifyColInfo['verifyCol']).setBackground(errorColor)
                    lError = True
                iCol += 1
                
            if lError:
                self.dr_table.setItem(rowPosition, iCol, QTableWidgetItem(str(1)))
            else:
                self.dr_table.setItem(rowPosition, iCol, QTableWidgetItem(str(0)))

        self.dr_table.setSortingEnabled(True)
        
