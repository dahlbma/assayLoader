import re, sys, os, logging, csv
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QDate, QUrl, QRegExp
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QComboBox, QDialog, QPushButton, QCheckBox, QSpacerItem, QSizePolicy, QMessageBox
from PyQt5 import QtGui
from PyQt5.QtGui import QIntValidator, QBrush, QColor, QRegExpValidator
import openpyxl
from pathlib import Path
from instruments import parseEnvision
import pandas as pd
import subprocess
from z_factor import *
from assaylib import *
from prepareHarmonyFile import *
from prepareEnvisionFile import *
from selectDataColumn import *
from doseResponseTable import DoseResponseTable, ScatterplotWidget
import platform
from inhibitionScatter import ScatterPlotWindow

# Get the operating system name
os_name = platform.system()

'''
{{name='raw' style='dot' x_label='conc' x_unit='M' x_values={1.25E-04,4.17E-05,1.39E-05,4.63E-06,1.54E-06,5.14E-07,1.71E-07,5.72E-08,1.91E-08,6.35E-09,2.12E-09} y_label='Inhibition' y_unit='%' y_values={105.07,94.19,65.84,23.12,1.48,-9.46,-13.04,-11.79,-10.53,-12.85,-15.35} y_error={0.42,1.23,3.24,2.85,1.32,1.18,0.28,0.93,1.27,1.53,1.12} }{name='fitsigmoidal' style='line' x_label='conc' x_unit='M' x_values={1.25E-04,4.17E-05,1.39E-05,4.63E-06,1.54E-06,5.14E-07,1.71E-07,5.72E-08,1.91E-08,6.35E-09,2.12E-09} y_label='inhibition' y_unit='%' logic50=-5.0512 hillslope=1.252 bottom=-12.8 top=109.6}}

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

        self.activation_rb.clicked.connect(self.toggleInhibition)
        self.inhibition_rb.clicked.connect(self.toggleInhibition)
        self.inhibition_rb.setChecked(True)
        
        self.saveExcel_btn.clicked.connect(self.doseResponseTable.saveToExcel)
        self.saveExcel_btn.setEnabled(True)
        

    def toggleInhibition(self):
        sender = self.sender()
        if sender == self.inhibition_rb and sender.isChecked():
            self.activation_rb.setChecked(False)
        elif sender == self.inhibition_rb and sender.isChecked():
            self.inhibition_rb.setChecked(False)


    def rowChanged(self, currentRowIndex):
        # Remove the old checkboxes
        for i in reversed(range(self.dataPoints_layout.count())):
            item = self.dataPoints_layout.itemAt(i)
            
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

        widget = self.doseResponseTable.cellWidget(iCurrentRow, self.doseResponseTable.graph_col)
        if isinstance(widget, ScatterplotWidget):
            #print(df)
            pass
        self.bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.dataPoints_layout.addItem(self.bottom_spacer)


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
        widget = self.doseResponseTable.cellWidget(row, 10)
        if isinstance(widget, ScatterplotWidget):
            df = widget.data_dict
        else:
            return

        iIndex = 0
        for checkValue in includedPoints:
            if checkValue == False:
                batch = df.iloc[iIndex]['Batch nr']
                compound = df.iloc[iIndex]['Compound ID']
                conc = df.iloc[iIndex]['finalConc_nM']
                self.deselectRow(batch, compound, conc)
            iIndex += 1
                
        selected_rows = df[includedPoints]
        widget.plot_scatter(selected_rows, self.yScale)
        self.doseResponseTable.updateTable(row, widget)


    def calcDR(self):
        self.saveExcel_btn.setEnabled(True)
        file = self.drInputFile_lab.text()
        if file == '':
            pass
        else:
            self.yScale = 'Inhibition %'
            if self.activation_rb.isChecked():
                self.yScale = 'Activation %'
            self.batch_df = self.doseResponseTable.generate_scatterplots(file, self.yScale, self)
            self.doseResponseTable.selectionModel().currentRowChanged.connect(self.rowChanged)


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
        prepared_path = os.path.join(subdirectory_path, "preparedEnvisionFiles")
        delete_all_files_in_directory(prepared_path)
        self.workingDirectory = prepared_path
        if prepared_path == "preparedEnvisionFiles":
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

        subdirectory_path = os.path.join(selected_directory, "preparedHarmonyFiles")
        if subdirectory_path == "preparedHarmonyFiles":
            return

        delete_all_files_in_directory(subdirectory_path)
        self.workingDirectory = subdirectory_path
        platemapFile, plateIdToFileMapping = findHarmonyFiles(self, subdirectory_path, selected_directory)
        self.generateDoseResponseInputFile(platemapFile, plateIdToFileMapping)


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
        
        combinedDataDf = pd.DataFrame()
        for index, row in rawDataFilesDf.iterrows():
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
        
        for index, row in platemapDf.iterrows():
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
        
        #fullPath = os.path.join(sBasePath, excel_file_path)
        resultDf.to_excel(excel_file_path, index=False)
        resultDf['deselected'] = False

        self.finalPreparedDR = resultDf
        assaylib.printPrepLog(self, f'File prepared for dose response computation saved:')
        assaylib.printPrepLog(self, f'{excel_file_path}', type='bold')
        self.drInputFile_lab.setText(excel_file_path)
