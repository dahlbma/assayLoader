import re, sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
import openpyxl
from assaylib import *

class LoaderScreen(QMainWindow):
    def __init__(self, token, test):
        super(LoaderScreen, self).__init__()
        self.token = token
        self.mod_name = "loader"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/loaderwindow.ui"), self)

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
            for i in self.spConfig:
                print(i, self.spConfig[i])
            h1 = [str(h) for h in self.spConfig]
            js = dbInterface.getDoseResponseConfig(self.token)
            self.drConfig = json.loads(js)
            h2 = [str(h) for h in self.drConfig]
        except:
            print("oops")   

        self.sp_table.setColumnCount(len(h1))
        self.sp_table.setHorizontalHeaderLabels(h1)
        self.dr_table.setColumnCount(len(h2))
        self.dr_table.setHorizontalHeaderLabels(h2)


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


    def verifyXlHeader(self, confHeader, xlHeader):
        print(confHeader)
        iCount = 0
        lAllOK = True
        for item in confHeader:
            if item == xlHeader[iCount]:
                print(item, xlHeader[iCount])
            else:
                lAllOK = False
                print(f'Column error: Expected column name "{item}" in position \
                {iCount +1}, but got "{xlHeader[iCount]}"')
            
            iCount += 1
        return lAllOK


    def populateAssayTable(self, workSheet):
        iRow = 0
        for row in workSheet.values:
            if iRow == 0:
                iRow +=1
                continue
            iRow += 1
            rowPosition = self.sp_table.rowCount()
            self.sp_table.insertRow(rowPosition)
            iCol = 0
            for value in row:
                self.sp_table.setItem(rowPosition, iCol, QTableWidgetItem(str(value)))
                iCol += 1
