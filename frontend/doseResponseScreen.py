import os, logging
from PyQt5.uic import loadUi
from PyQt5.QtCore import QRegExp, QDate, Qt
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QDialog
from PyQt5.QtWidgets import QCheckBox, QMessageBox
from PyQt5.QtGui import QBrush, QColor, QRegExpValidator, QCursor
import pandas as pd
from z_factor import *
from assaylib import *
from prepareHarmonyFile import *
from prepareEnvisionFile import *
from selectDataColumn import *
from doseResponseTable import ScatterplotWidget
import platform
#from inhibitionScatter import ScatterPlotWindow

# Get the operating system name
os_name = platform.system()

'''
1.25E-04, 105.07
4.17E-05, 94.19
1.39E-05, 65.84
4.63E-06, 23.12
1.54E-06, 1.48
5.14E-07, -9.46
1.71E-07, -13.04
5.72E-08, -11.79
1.91E-08, -10.53
6.35E-09, -12.85
2.12E-09, -15.35

x_values={1.25E-04, 4.17E-05, 1.39E-05, 4.63E-06, 1.54E-06, 5.14E-07, 1.71E-07, 5.72E-08, 1.91E-08, 6.35E-09, 2.12E-09 }
y_values={105.07, 94.19, 65.84, 23.12, 1.48, -9.46, -13.04, -11.79, -10.53, -12.85, -15.35 }
{
   {
      name='raw' style='dot' x_label='conc' x_unit='M'
      x_values={1.25E-04, 4.17E-05, 1.39E-05, 4.63E-06, 1.54E-06, 5.14E-07, 1.71E-07, 5.72E-08, 1.91E-08, 6.35E-09, 2.12E-09 }
      y_label='Inhibition'
      y_unit='%'
      y_values={105.07, 94.19, 65.84, 23.12, 1.48, -9.46, -13.04, -11.79, -10.53, -12.85, -15.35 }
      y_error={0.42, 1.23, 3.24, 2.85, 1.32, 1.18, 0.28, 0.93, 1.27, 1.53, 1.12 }
   }{
      name='fitsigmoidal' style='line' x_label='conc' x_unit='M'
      x_values={1.25E-04, 4.17E-05, 1.39E-05, 4.63E-06, 1.54E-06, 5.14E-07, 1.71E-07, 5.72E-08, 1.91E-08, 6.35E-09, 2.12E-09 }
      y_label='inhibition'
      y_unit='%'
      logic50=-5.0512
      hillslope=1.252
      bottom=-12.8
      top=109.6
   }
}
'''

saSearchTables = {
    "DR Sandbox": "assay_test.lcb_dr",
    "DR": "assay.lcb_dr"
}


def userInfo(sMessage):
    info_dialog = QMessageBox()

    # Set the icon and text of the dialog
    info_dialog.setIcon(QMessageBox.Information)
    info_dialog.setText(sMessage)
    info_dialog.setWindowTitle("Information")

    # Add a button to the dialog
    info_dialog.addButton(QMessageBox.Ok)
    
    # Show the dialog
    info_dialog.exec_()


class DoseResponseScreen(QMainWindow):
    from assaylib import gotoSP
    def __init__(self, token, test):
        super(DoseResponseScreen, self).__init__()
        self.test = test
        self.token = token
        self.mod_name = "loader"
        self.logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/doseResponseTab.ui"), self)
        self.rVolume = None
        self.sDataColName = ''
        self.finalWellVolumeMicroliter_eb.textChanged.connect(self.wellVolumeChanged)
        regex = QRegExp("[0-9]+.?[0-9]*")  # Only digits 1-9 and a single dot
        validator = QRegExpValidator(regex, self.finalWellVolumeMicroliter_eb)
        self.finalWellVolumeMicroliter_eb.setValidator(validator)

        # This is the dataframe holding all the data to plot
        self.finalPreparedDR = None
        self.pathToFinalPreparedDR = None
        self.pathToFinalPreparedDR_deselects = None
        
        self.posCtrl_eb.setText('CTRL')
        
        self.selectHarmonyDirectory_btn.setEnabled(False)
        self.selectHarmonyDirectory_btn.clicked.connect(self.selectHarmonyDirectory)
        self.workingDirectory = ''

        self.selectEnvisionPlateToFile_btn.setEnabled(False)
        self.selectEnvisionPlateToFile_btn.clicked.connect(self.selectEnvisionPlateToFile)
        self.workingDirectory = ''
        
        self.drInputFile_lab.setText('')
        self.selectDRInput_btn.clicked.connect(self.selectDRInputFile)
        self.dataColumn_lab.setText('')

        self.calculateDR_btn.clicked.connect(self.calcDR)
        self.goto_sp_btn.clicked.connect(self.gotoSP)
        self.dataPointCheckboxes = []
        self._row_changed_slot = None # To keep track of callback for change row
        self.activation_rb.clicked.connect(self.toggleInhibition)
        self.inhibition_rb.clicked.connect(self.toggleInhibition)
        self.inhibition_rb.setChecked(True)
        
        self.saveExcel_btn.clicked.connect(self.doseResponseTable.saveToExcel)
        self.saveExcel_btn.setEnabled(True)

        self.module_tab_wg.currentChanged.connect(self.tab_switched)

        self.dr_tab_col_batch = 0
        self.dr_tab_col_compound = 1
        self.dr_tab_col_project = 2
        self.dr_tab_col_target = 3
        self.dr_tab_col_plate = 4
        self.dr_tab_col_assay_type = 5
        self.dr_tab_col_detection_type = 6
        self.dr_tab_col_cmax = 7
        self.dr_tab_col_top = 8
        self.dr_tab_col_bottom = 9
        self.dr_tab_col_slope = 10
        self.dr_tab_col_ic50 = 11
        self.dr_tab_col_ec50 = 12
        self.dr_tab_col_icmax = 13
        self.dr_tab_col_graph = 14
        self.dr_tab_col_test_date = 15
        self.dr_tab_col_operator = 16
        self.dr_tab_col_eln = 17
        self.dr_tab_col_confirmed = 18
        self.dr_tab_col_comment = 19

        self.ic50_ec50 = 'IC50'
        self.not_ic50_ec50 = 'EC50'
        
        self.populateScreenData()
        
        self.updateGrid_btn.clicked.connect(self.updateGrid)
        self.loadAssayFile_btn.clicked.connect(self.loadAssayDataFromFile)
        self.saveData_btn.clicked.connect(self.saveDrToDb)
        
        self.search_btn.clicked.connect(self.searchDR)

    def searchDR(self):
        sProject = self.searchProject_cb.currentText()
        sTable = self.searchTable_cb.currentText()

        selectedTable_key = self.searchTable_cb.currentText()
        selectedTable_value = saSearchTables.get(selectedTable_key)


        print(selectedTable_value)

        df, lStatus = dbInterface.getDrData(self.token, sProject, selectedTable_value)
        if not lStatus or df.empty:
            userInfo("No data found")
            return

        #self.doseResponseTable.populate_table(df)


    def populateScreenData(self):
        saProjects = dbInterface.getProjects(self.token)
        saDrProjects = dbInterface.getDrProjects(self.token, 'assay.lcb_dr')

        self.project_cb.addItems(saProjects)
        self.searchProject_cb.addItems(saDrProjects)
        self.searchTable_cb.addItems(saSearchTables.keys())

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
            "DR Sandbox table",
            "Dose response"
        ]
        self.targetTable_cb.addItems(saTargetTables)
        
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

        self.testDate.setDate(QDate.currentDate())


    def loadAssayDataFromFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        loadAssayDataDialog = QFileDialog()
        loadAssayDataDialog.setOptions(options)

        fileName, _ = loadAssayDataDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv *.CSV)")

        if not fileName:
            return


    def findColumnNumber(self, sCol):
        iCol = -1
        for col in range(self.dr_table.columnCount()):
            header_item = self.dr_table.horizontalHeaderItem(col)
            header_text = header_item.text()

            if header_text == sCol:
                iCol = col
                break
        return iCol


    def saveDrToDb(self):
        # If there is no data do nothing.
        if self.dr_table.rowCount() == 0:
            return
        
        def getDateColumn():
            column_count = self.dr_table.columnCount()
            # Initialize an empty list to store column names
            column_names = []

            # Loop through each column index
            for col in range(column_count):
                # Get the horizontal header item for the column
                header_item = self.dr_table.horizontalHeaderItem(col)
    
                # Check if the header item is not None
                if header_item.text() == 'experiment_date':
                    return col
        iDateCol = getDateColumn()
        item = self.dr_table.item(0, iDateCol)
        
        #if self.dr_table.rowCount() > 0 and item is not None and item.text().strip() == "":
        if self.dr_table.rowCount() > 0:
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

            self.populate_table(df, 'Cmax', error=True)
            self.populate_table(df, 'Y max', error=True)
            self.populate_table(df, 'M min', error=True)
            self.populate_table(df, 'Hill', error=True)
            self.populate_table(df, 'IC50', error=True)
            self.populate_table(df, 'EC50', error=True)
            self.populate_table(df, 'I Cmax', error=True)
            self.populate_table(df, 'E Cmax', error=True)

            self.populate_table(df, 'test_date', error=True)
            self.populate_table(df, 'operator', error=True)
            self.populate_table(df, 'eln', error=True)
            self.populate_table(df, 'comment', error=True)

        repopulate_data = []
        def uploadRows(rows, targetTable):
            if accumulated_rows == []:
                return

            sRes, lStatus = dbInterface.saveDrRowToDb(self.token, accumulated_rows, targetTable)
            
            if lStatus == False:
                for ro in sRes:
                    repopulate_data.append(ro)

        accumulated_rows = []
        iAccumulator_count = 0
        iRowsBatch = 3
        targetTable = self.targetTable_cb.currentText()
        self.popup = PopUpProgress(f'Uploading data')
        self.popup.show()
        iNrOfRows = self.dr_table.rowCount()
        iTick = 0
        rProgressSteps = (iRowsBatch/iNrOfRows)*100

        QApplication.setOverrideCursor(Qt.WaitCursor)
        for row in range(self.dr_table.rowCount()):
            row_dict = {}
            for col in range(self.dr_table.columnCount()):
                header_item = self.dr_table.horizontalHeaderItem(col)
                item = self.dr_table.item(row, col)
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

        self.dr_table.setRowCount(0)
        dfRepopulate = pd.DataFrame(repopulate_data)
        repopulate_errors(dfRepopulate)
        QApplication.restoreOverrideCursor()
        self.popup.obj.proc_counter(100)
        self.popup.close()


    def populate_table(self, dataframe, column_name, insertRows=False, error=False):
        
        def insertRow(iNrOfRows, iNrOfCols):
            iLocalCol = 0
            for iRow in range(iNrOfRows):
                self.dr_table.insertRow(iRow)
                for iCol in range(iNrOfCols):
                    item = QTableWidgetItem(str(''))
                    self.dr_table.setItem(iRow, iCol, item)

        if insertRows:
            insertRow(dataframe.shape[0], self.dr_table.columnCount())

        iCol = self.findColumnNumber(column_name)

        if iCol == -1:
            self.printQcLog(f"Couldn't find column {column_name}", 'error')
            return
        
        # Populate the specified column of the table with data from the DataFrame
        iRow_index = 0
        for row_index, row_data in dataframe.iterrows():
            item = QTableWidgetItem(str(row_data[column_name]))
            self.dr_table.setItem(iRow_index, iCol, item)
            if error == True:
                item.setBackground(QBrush(QColor('red')))
            iRow_index += 1


    def populateColumn(self, sCol, sValue):
        iNrRows = self.dr_table.rowCount()
        iCol = self.findColumnNumber(sCol)

        if iCol == -1:
            print(sCol, sValue, iCol)
        
        iRow_index = 0
        for iRow_index in range(iNrRows):
            item = QTableWidgetItem(str(sValue))
            self.dr_table.setItem(iRow_index, iCol, item)


    def printQcLog(self, s, type='', beep=False):
        # What should we do here?
        pass


    def updateGrid(self):
        print('updateGrid')
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
        #self.populateColumn('comment', self.comment_eb.text())
        self.populateColumn('eln', self.eln_eb.text())


    def populate_load_data(self, df):
        self.dr_table.setRowCount(len(df))
        self.populateColumn('Confirmed', '')        
        
        for row_index, row_data in df.iterrows():
            batch_id = str(row_data["Batch"])
            compound_id = str(row_data["Compound"])
            cmax = str(row_data["Max Conc nM"])
            if self.ic50_ec50 == 'IC50':
                icmax = str(row_data["ICMax"])
                ecmax = ''
            else:
                icmax = ''
                ecmax = str(row_data["ICMax"])
                
            c50 = str(row_data[self.ic50_ec50])
            not_c50 = ''
            slope = str(row_data["Slope"])
            top = str(row_data["Top"])
            bottom = str(row_data["Bottom"])
            sComment = str(row_data["comment"])
            
            sGraph = self.doseResponseTable.cellWidget(row_index, self.doseResponseTable.graph_col).sGraph
            sConfirmed = self.doseResponseTable.cellWidget(row_index, self.doseResponseTable.graph_col).confirmed
            sComment = self.doseResponseTable.cellWidget(row_index, self.doseResponseTable.graph_col).comment
            
            self.dr_table.setItem(row_index, self.dr_tab_col_batch, QTableWidgetItem(batch_id))
            self.dr_table.setItem(row_index, self.dr_tab_col_compound, QTableWidgetItem(compound_id))
            
            self.dr_table.setItem(row_index, self.findColumnNumber('Cmax'), QTableWidgetItem(cmax))
            self.dr_table.setItem(row_index, self.findColumnNumber('I Cmax'), QTableWidgetItem(icmax))
            self.dr_table.setItem(row_index, self.findColumnNumber('E Cmax'), QTableWidgetItem(ecmax))
            self.dr_table.setItem(row_index, self.findColumnNumber(self.ic50_ec50), QTableWidgetItem(c50))
            self.dr_table.setItem(row_index, self.findColumnNumber(self.not_ic50_ec50), QTableWidgetItem(not_c50))
            self.dr_table.setItem(row_index, self.findColumnNumber('Hill'), QTableWidgetItem(slope))

            self.dr_table.setItem(row_index, self.findColumnNumber('Y Max'), QTableWidgetItem(top))
            self.dr_table.setItem(row_index, self.findColumnNumber('M Min'), QTableWidgetItem(bottom))
            self.dr_table.setItem(row_index, self.findColumnNumber('comment'), QTableWidgetItem(sComment))
            self.dr_table.setItem(row_index, self.findColumnNumber('Graph'), QTableWidgetItem(sGraph))
            self.dr_table.setItem(row_index, self.findColumnNumber('Confirmed'), QTableWidgetItem(sConfirmed))


    def tab_switched(self, index):
        tab_text = self.module_tab_wg.tabText(index)

        self.populateColumn('IC50', '')
        self.populateColumn('EC50', '')
        
        if tab_text == "DR load data":
            print("User switched to dr_load_data tab")
            df = self.doseResponseTable.qtablewidget_to_dataframe()
            if len(df) == 0:
                return
            self.populate_load_data(df)


    def toggleInhibition(self):
        sender = self.sender()
        if sender == self.inhibition_rb and sender.isChecked():
            self.activation_rb.setChecked(False)
            self.doseResponseTable.changeIC50_EC50_heading('IC50')
            self.ic50_ec50 = 'IC50'
            self.not_ic50_ec50 = 'EC50'
        elif sender == self.activation_rb and sender.isChecked():
            self.inhibition_rb.setChecked(False)
            self.doseResponseTable.changeIC50_EC50_heading('EC50')
            self.ic50_ec50 = 'EC50'
            self.not_ic50_ec50 = 'IC50'


    def connect_row_changed_slot(self, slot_function):
        """Connects the currentRowChanged signal to a slot."""
        if self._row_changed_slot: # Disconnect old one if exists (e.g. if re-connecting to new slot)
            try:
                self.doseResponseTable.selectionModel().currentRowChanged.disconnect(self._row_changed_slot)
            except TypeError: # Handle case where it might already be disconnected
                pass
        self._row_changed_slot = slot_function
        self.doseResponseTable.selectionModel().currentRowChanged.connect(slot_function)

    
    def disconnect_row_changed_slot(self):
        """Disconnects the currentRowChanged signal."""
        if self._row_changed_slot:
            try:
                self.doseResponseTable.selectionModel().currentRowChanged.disconnect(self._row_changed_slot)
            except TypeError:
                #print("Row changed slot already disconnected (or never connected).")
                pass
            self._row_changed_slot = None # Clear reference

        
    def rowChanged(self, currentRowIndex):
        # Remove the old checkboxes
        while self.dataPoints_layout.count():
            item = self.dataPoints_layout.takeAt(0)
            
            if item.widget():
                widg = item.widget()
                self.dataPoints_layout.removeWidget(widg)
            try:
                widg.setParent(None)
                widg.deleteLater()
            except Exception as e:
                pass
        
        iCurrentRow = currentRowIndex.row()
        df = pd.DataFrame()
        widget = self.doseResponseTable.cellWidget(iCurrentRow, self.doseResponseTable.graph_col)
        if isinstance(widget, ScatterplotWidget):
            df = widget.data_dict
        else:
            print('No data')
        # Insert new checkboxes here
        for index, row in df.iterrows():
            conc = "{:.1f}".format(row['finalConc_nM'])
            new_checkbox = QCheckBox(f"{conc}")
            new_checkbox.setChecked(True)
            self.dataPoints_layout.insertWidget(len(self.dataPointCheckboxes), new_checkbox)
            self.dataPointCheckboxes.append(new_checkbox)
            new_checkbox.stateChanged.connect(lambda state: self.checkbox_changed(new_checkbox, state, iCurrentRow))

        #widget = self.doseResponseTable.cellWidget(iCurrentRow, self.doseResponseTable.graph_col)
        #if isinstance(widget, ScatterplotWidget):
        #    pass
        #self.bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        #self.dataPoints_layout.addItem(self.bottom_spacer)


    def checkbox_changed(self, checkbox, state, iCurrentRow):
        # state == 2   => checked
        res = []
        for i in range(self.dataPoints_layout.count()):
            item = self.dataPoints_layout.itemAt(i)
            widg = item.widget()
            try:
                if widg.isChecked():
                    res.append(True)
                else:
                    res.append(False)
            except:
                pass
        self.updatePlot(iCurrentRow, res)
        self.saveExcel_btn.setEnabled(True)


    def updatePlot(self, row, includedPoints):
        df = None
        widget = self.doseResponseTable.cellWidget(row, 11)
        if isinstance(widget, ScatterplotWidget):
            df = widget.data_dict
        else:
            return
        
        iIndex = 0
        maxConc = 0
        for checkValue in includedPoints:
            thisConc = df.iloc[iIndex]['finalConc_nM']
            if checkValue == False:
                batch = df.iloc[iIndex]['Batch nr']
                compound = df.iloc[iIndex]['Compound ID']
                conc = thisConc
                self.deselectRow(batch, compound, conc)
            else:
                if thisConc > maxConc:
                    maxConc = thisConc
            iIndex += 1

        selected_rows = df[includedPoints]
        widget.plot_scatter(selected_rows, self.yScale)
        self.doseResponseTable.updateTable(row, widget)
        self.doseResponseTable.updateMaxConc(row, maxConc)
        
        if self.parentWidget() and self.parentWidget().layout():
            self.parentWidget().layout().invalidate()
        

    def calcDR(self):
        self.saveExcel_btn.setEnabled(True)
        file = self.drInputFile_lab.text()
        if file == '':
            pass
        else:
            self.yScale = 'Inhibition %'
            if self.activation_rb.isChecked():
                self.yScale = 'Activation %'

            self.disconnect_row_changed_slot()
            self.batch_df = self.doseResponseTable.generate_scatterplots(file, self.yScale, self)
            self.connect_row_changed_slot(self.rowChanged)
            #self.doseResponseTable.selectionModel().currentRowChanged.connect(self.rowChanged)


    def deselectRow(self, batch, compound, conc):
        self.finalPreparedDR.loc[(self.finalPreparedDR['Batch nr'] == batch) & (self.finalPreparedDR['Compound ID'] == compound) & (self.finalPreparedDR['finalConc_nM'] == conc), 'deselected'] = True

        
    def selectDRInputFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self,
                                                   "QFileDialog.getOpenFileName()",
                                                   "",
                                                   "Excel Files (*.xlsx);;All Files (*)",
                                                   options=options)
        if file_name:
            self.drInputFile_lab.setText(file_name)
        

    def wellVolumeChanged(self, sVolume):
        try:
            self.rVolume = float(sVolume)
        except:
            self.selectHarmonyDirectory_btn.setEnabled(False)
            self.rVolume = None
            return
        self.selectHarmonyDirectory_btn.setEnabled(True)
        self.selectEnvisionPlateToFile_btn.setEnabled(True)
        
    '''
    def generatePlatemap(self):
        print('generate platemap here')
        #self.generateCurvefittingInput_btn.setEnabled(True)
        
    def generateCurvefittingInput(self):
        print('generate curvefitting input here')
    '''

    def selectEnvisionPlateToFile(self):
        subdirectory_path = ''
        options = QFileDialog.Options()
        #options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,
                                                  "Select Excel File", "", "Excel Files (*.xlsx *.xls)",
                                                  options=options)
        if fileName:
            subdirectory_path = os.path.dirname(fileName)
        print(f'subdirectory_path: {subdirectory_path}')
        prepared_path = os.path.join(subdirectory_path, "assayLoaderEnvisionFiles")
        delete_all_files_in_directory(prepared_path)
        self.workingDirectory = prepared_path
        if prepared_path == "assayLoaderEnvisionFiles":
            return

        platemapFile, plateIdToFileMapping = findEnvisionFiles(self, prepared_path, fileName)
        self.generateDoseResponseInputFile(platemapFile, plateIdToFileMapping)


    def selectHarmonyDirectory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog  # Use the native file dialog
        directory_dialog = QFileDialog()
        directory_dialog.setOptions(options)
        # Set the file mode to DirectoryOnly to allow selecting directories only
        directory_dialog.setFileMode(QFileDialog.DirectoryOnly)
        # Show the directory dialog
        selected_directory = directory_dialog.getExistingDirectory(self, 'Open Directory', '')

        subdirectory_path = os.path.join(selected_directory, "assayLoaderHarmonyFiles")
        if subdirectory_path == "assayLoaderHarmonyFiles":
            return

        delete_all_files_in_directory(subdirectory_path)
        self.workingDirectory = subdirectory_path
        platemapFile, plateIdToFileMapping = findHarmonyFiles(self, subdirectory_path, selected_directory)
        self.generateDoseResponseInputFile(platemapFile, plateIdToFileMapping)


    def remove_single_row_compounds(self, df):
        """
        Removes rows from a DataFrame where 'Compound ID' appears only once. (No DR calulation for these)
        
            Args:
            df (pd.DataFrame): The input DataFrame.
            
            Returns:
            pd.DataFrame: The DataFrame with single-row compounds removed.
            """
        
        compound_counts = df['Batch nr'].value_counts()
        compounds_to_keep = compound_counts[compound_counts > 1].index.tolist()
        filtered_df = df[df['Batch nr'].isin(compounds_to_keep)]
        return filtered_df


    def generateDoseResponseInputFile(self, platemapFile, plateIdToFileMapping):
        platemap_xlsx = os.path.abspath(platemapFile)
        sBasePath = os.path.dirname(platemap_xlsx)
        platemapDf = pd.read_excel(platemap_xlsx)
        
        rawDataFilesDf = pd.read_excel(plateIdToFileMapping)

        # Final volume in nano liter (nL)
        final_volume = float(self.finalWellVolumeMicroliter_eb.text())*1000.0
        if len(platemapDf) > 0:
            platemapDf['finalConc_nM'] = (platemapDf['Conc mM']* 1000000 * platemapDf['volume nL']) / final_volume
        else:
            assaylib.printPrepLog(self, f'Error: No data lines in platemap, are the plates loaded into Cello?', 'error')
            return
        
        rawDatafile = rawDataFilesDf.iloc[0]['file']
        saDataColumns = assaylib.findDataColumns(rawDatafile)
        dataColDialog = SelectDataColumn(saDataColumns)
        if dataColDialog.exec_() == QDialog.Accepted:
            self.sDataColName = dataColDialog.selectedColumn
            self.dataColumn_lab.setText(dataColDialog.selectedColumn)

        sDataColName = self.sDataColName
        if sDataColName == '':
            return

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        
        combinedDataDf = pd.DataFrame()
        for index, row in rawDataFilesDf.iterrows():
            QApplication.processEvents()
            plate = row['plate']
            file_path = row['file']
        
            rawDataDf = pd.read_csv(file_path)
            plates = [plate] * len(rawDataDf)
            rawDataDf.insert(0, 'plate', plates)
            if len(combinedDataDf) == 0:
                combinedDataDf = rawDataDf
            else:
                combinedDataDf = pd.concat([combinedDataDf, rawDataDf], ignore_index=True)
        
        platemapDf['rawData'] = ''
        assaylib.printPrepLog(self, 'Reformatting input data\n')

        iDataCounter = 0
        for index, row in platemapDf.iterrows():
            iDataCounter += 1
            if iDataCounter % 20 == 0:
                assaylib.printPrepLog(self, '.')
            plate_id = row['Platt ID']
            well = row['Well']

            matching_row = combinedDataDf[(combinedDataDf['plate'] == plate_id) & (combinedDataDf['Well'] == well)]
            if not matching_row.empty:
                # Update 'rawData' in platemapDf
                platemapDf.at[index, 'rawData'] = matching_row[sDataColName].values[0]
        
        # Remove columns 'Conc mM' and 'volume nL'
        columns_to_remove = ['Conc mM', 'volume nL']
        platemapDf = platemapDf.drop(columns=columns_to_remove)
        
        excel_file_path = os.path.join(self.workingDirectory, 'dose_response_platemap.xlsx')
        platemapDf.to_excel(excel_file_path, index=False)

        
        # Group by 'Batch' and calculate mean and yStd
        grouped_df = platemapDf.groupby(['Batch nr',
                                         'Compound ID',
                                         'finalConc_nM'])['rawData'].agg(['mean', 'std']).reset_index()
        resultDf = grouped_df.rename(columns={'mean': 'yMean', 'std': 'yStd'})
        sCtrl = self.posCtrl_eb.text()
        try:
            meanPosCtrl = resultDf.loc[resultDf["Compound ID"] == sCtrl, "yMean"].values[0]
            meanNegCtrl = resultDf.loc[resultDf["Compound ID"] == "DMSO", "yMean"].values[0]
        except:
            userInfo(f'''No controls named {sCtrl} in the dataset''')
            QApplication.restoreOverrideCursor()
            return
        
        resultDf['inhibition'] = 100*(1-(resultDf['yMean']-meanPosCtrl)/(meanNegCtrl-meanPosCtrl))

        # Calculate the scalingfactor between the raw data and the inhibition values
        first_CBK_row = resultDf[resultDf['Compound ID'].str.startswith('CBK')].head(1)
        print(first_CBK_row)
        yVal = first_CBK_row['yMean'].values[0]
        yInhib = first_CBK_row['inhibition'].values[0]
        scaleFactor = abs(yVal / yInhib)
        print(f'Scale factor: {scaleFactor}')
        resultDf['yStd'] = resultDf['yStd'] / scaleFactor
        
        # Rename columns if needed
        resultDf = resultDf.rename(columns={'Batch': 'Batch', 'rawData': 'yMean'})

        excel_file_path = os.path.join(self.workingDirectory, 'finalPreparedDR.xlsx')
        self.pathToFinalPreparedDR = excel_file_path

        excel_file_path_deselected = os.path.join(self.workingDirectory, 'finalPreparedDR_deselected_datapoints.xlsx')
        self.pathToFinalPreparedDR_deselects = excel_file_path_deselected

        resultDf = self.remove_single_row_compounds(resultDf)
        
        #fullPath = os.path.join(sBasePath, excel_file_path)
        resultDf.to_excel(excel_file_path, index=False)
        resultDf['deselected'] = False
        QApplication.restoreOverrideCursor()

        self.finalPreparedDR = resultDf
        assaylib.printPrepLog(self, f'File prepared for dose response computation saved:')
        assaylib.printPrepLog(self, f'{excel_file_path}', type='bold')
        self.drInputFile_lab.setText(excel_file_path)
