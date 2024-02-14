import re, sys, os, logging, glob, csv
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QDate, QUrl, QRegExp
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QComboBox, QDateEdit, QDialog, QPushButton
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
import platform
from inhibitionScatter import ScatterPlotWindow


# Get the operating system name
os_name = platform.system()


class SelectDataColumn(QDialog):
    def __init__(self, parent, columns):
        super().__init__()

        self.setWindowTitle("Select a datacolumn")
        self.columns = columns
        self.parent = parent
        
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Create a combo box
        self.comboBox = QComboBox()
        self.comboBox.addItems(self.columns)
        layout.addWidget(self.comboBox)

        # Create a button to confirm selection
        selectButton = QPushButton("Select")
        selectButton.clicked.connect(self.onSelect)
        layout.addWidget(selectButton)

        self.setLayout(layout)

    def onSelect(self):
        # Get the selected item
        selected_item = self.comboBox.currentText()
        self.parent.dataColumn_lab.setText(selected_item)
        self.parent.sDataColName = selected_item
        self.close()


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

        self.drInputFile_lab.setText('')
        self.selectDRInput_btn.clicked.connect(self.selectDRInputFile)
        self.dataColumn_lab.setText('')
        self.goto_sp_btn.clicked.connect(self.gotoSP)        

    def selectDRInputFile(self):
        print('DR input clicked')
        
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

        assaylib.resetPrepLog(self)
        
        platemapFile, plateIdToFileMapping = findHarmonyFiles(self, subdirectory_path, selected_directory)
        self.generateDoseResponseInputFile(platemapFile, plateIdToFileMapping)
        

    def generateCurvefittingInput(self):
        print('generate curvefitting input here')
        

    def generateDoseResponseInputFile(self, platemapFile, plateIdToFileMapping):
        platemap_xlsx = os.path.abspath(platemapFile)
        #sDataColName = 'Cell Selected - Number of Spots - Mean per Well'
        sBasePath = os.path.dirname(platemap_xlsx)
        platemapDf = pd.read_excel(platemap_xlsx)
        
        rawDataFilesDf = pd.read_excel(plateIdToFileMapping)
        
        # Final volume in nano liter (nL)
        final_volume = float(self.finalWellVolumeMicroliter_eb.text())*1000.0
        platemapDf['finalConc_nL'] = (platemapDf['Conc mM']* 1000000 * platemapDf['volume nL']) / final_volume

        rawDatafile = rawDataFilesDf.iloc[0]['file']
        saDataColumns = assaylib.findDataColumns(rawDatafile)
        dataColDialog = SelectDataColumn(self, saDataColumns)
        if dataColDialog.exec_() == QDialog.Accepted:
            sDataColName = dataColDialog.result()
            self.dataColumn_lab.setText(sDataColName)

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
        
        excel_file_path = 'prepare_platemap.xlsx'
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

        excel_file_path = 'finalPreparedDR.xlsx'
        
        fullPath = os.path.join(sBasePath, excel_file_path)
        resultDf.to_excel(fullPath, index=False)
        assaylib.printPrepLog(self, f'File prepared for dose response computation saved:')
        assaylib.printPrepLog(self, f'{fullPath}', type='bold')
        self.drInputFile_lab.setText(fullPath)

