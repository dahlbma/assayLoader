import re, sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
import openpyxl
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
        #self.dr_table.setColumnCount(len(dr_header))
        #self.dr_table.setHorizontalHeaderLabels(dr_header)


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.loader_tab_wg.currentIndex() == 1:
                return
            else: # tab 0, no btn
                return

    def tabChanged(self):
        page_index = self.loader_tab_wg.currentIndex()
        if page_index == 0:
            return
        elif page_index == 1:
            return

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
                if iCol == self.spVerifyColInfo['verifyCol'] and value not in saCompIds:
                    self.sp_table.item(rowPosition, self.spVerifyColInfo['verifyCol']).setBackground(errorColor)
                    lError = True
                iCol += 1
                
            if lError:
                self.sp_table.setItem(rowPosition, iCol, QTableWidgetItem(str(1)))
            else:
                self.sp_table.setItem(rowPosition, iCol, QTableWidgetItem(str(0)))

        self.sp_table.setSortingEnabled(True)
        
