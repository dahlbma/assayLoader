import re, sys, os, logging, glob, csv
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QDate, QUrl, QRegExp
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QComboBox, QDateEdit, QDialog, QPushButton, QCheckBox, QSpacerItem, QSizePolicy
from PyQt5 import QtGui
from PyQt5.QtGui import QIntValidator, QBrush, QColor, QValidator, QRegExpValidator
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import openpyxl
from pathlib import Path
from instruments import parseEnvision
import pandas as pd
import subprocess
from z_factor import *
from assaylib import *
from prepareHarmonyFile import *
from selectDataColumn import *
from doseResponseTable import DoseResponseTable, ScatterplotWidget
import platform
from inhibitionScatter import ScatterPlotWindow


# Get the operating system name
os_name = platform.system()


class DoseResponseScreen(QMainWindow):
    from assaylib import gotoSP
    def __init__(self, token, test):
        super(DoseResponseScreen, self).__init__()
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

        self.selectHarmonyDirectory_btn.setEnabled(False)
        self.selectHarmonyDirectory_btn.clicked.connect(self.selectHarmonyDirectory)
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
            conc = "{:.1f}".format(row['finalConc_nL'])
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


    def updatePlot(self, row, includedPoints):
        df = None
        widget = self.doseResponseTable.cellWidget(row, 10)
        if isinstance(widget, ScatterplotWidget):
            df = widget.data_dict
        else:
            return

        selected_rows = df[includedPoints]
        #print(selected_rows)
        widget.plot_scatter(selected_rows, self.yScale)
        self.doseResponseTable.updateTable(row, widget)


    def calcDR(self):
        file = self.drInputFile_lab.text()
        if file == '':
            pass
        else:
            self.yScale = 'Inhibition %'
            if self.activation_rb.isChecked():
                self.yScale = 'Activation %'
            self.batch_df = self.doseResponseTable.generate_scatterplots(file, self.yScale)
            self.doseResponseTable.selectionModel().currentRowChanged.connect(self.rowChanged)

        
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
        

    def generatePlatemap(self):
        print('generate platemap here')
        #self.generateCurvefittingInput_btn.setEnabled(True)


    def selectHarmonyDirectory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog  # Use the native file dialog
        directory_dialog = QFileDialog()
        directory_dialog.setOptions(options)
        # Set the file mode to DirectoryOnly to allow selecting directories only
        directory_dialog.setFileMode(QFileDialog.DirectoryOnly)
        # Show the directory dialog
        selected_directory = directory_dialog.getExistingDirectory(self, 'Open Directory', '')

        subdirectory_path = os.path.join(selected_directory, "preparedHaronyFiles")
        if subdirectory_path == "preparedHaronyFiles":
            return

        self.workingDirectory = subdirectory_path
        platemapFile, plateIdToFileMapping = findHarmonyFiles(self, subdirectory_path, selected_directory)
        self.generateDoseResponseInputFile(platemapFile, plateIdToFileMapping)
        

    def generateCurvefittingInput(self):
        print('generate curvefitting input here')
        

    def generateDoseResponseInputFile(self, platemapFile, plateIdToFileMapping):
        platemap_xlsx = os.path.abspath(platemapFile)
        sBasePath = os.path.dirname(platemap_xlsx)
        platemapDf = pd.read_excel(platemap_xlsx)
        
        rawDataFilesDf = pd.read_excel(plateIdToFileMapping)
        
        # Final volume in nano liter (nL)
        final_volume = float(self.finalWellVolumeMicroliter_eb.text())*1000.0
        platemapDf['finalConc_nL'] = (platemapDf['Conc mM']* 1000000 * platemapDf['volume nL']) / final_volume
        print(rawDataFilesDf)
        
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
        
        # Group by 'Batch' and calculate mean and yVariance
        grouped_df = platemapDf.groupby(['Batch nr',
                                         'Compound ID',
                                         'finalConc_nL'])['rawData'].agg(['mean', 'std']).reset_index()
        resultDf = grouped_df.rename(columns={'mean': 'yMean', 'std': 'yStd'})
        
        ### Do proper calculation here instead!!!
        ### This is just some dummy scaling 12 (max inhibition value) to be close to 100.
        ### Need proper calculation here
        resultDf['yStd'] = resultDf['yStd'] * 12
        
        meanPosCtrl = resultDf.loc[resultDf["Compound ID"] == "CTRL", "yMean"].values[0]
        meanNegCtrl = resultDf.loc[resultDf["Compound ID"] == "DMSO", "yMean"].values[0]
        
        resultDf['inhibition'] = 100*(1-(resultDf['yMean']-meanPosCtrl)/(meanNegCtrl-meanPosCtrl))
        
        # Rename columns if needed
        resultDf = resultDf.rename(columns={'Batch': 'Batch', 'rawData': 'yMean'})

        excel_file_path = os.path.join(self.workingDirectory, 'finalPreparedDR.xlsx')
        
        #fullPath = os.path.join(sBasePath, excel_file_path)
        resultDf.to_excel(excel_file_path, index=False)
        assaylib.printPrepLog(self, f'File prepared for dose response computation saved:')
        assaylib.printPrepLog(self, f'{excel_file_path}', type='bold')
        self.drInputFile_lab.setText(excel_file_path)

