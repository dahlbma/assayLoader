import re, sys, os, logging, csv
from PyQt5.uic import loadUi
from PyQt5.QtCore import QRegExp, QDate, Qt
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QComboBox, QDialog, QPushButton
from PyQt5.QtWidgets import QCheckBox, QSpacerItem, QSizePolicy, QMessageBox
import openpyxl
from pathlib import Path
import pandas as pd
from assaylib import *
from prepareHarmonyFile import *
from prepareEnvisionFile import *
from selectDataColumn import *


class DrSearch:
    def __init__(self, parent):
        self.parent = parent  # Reference to DoseResponseScreen or needed context
        self.saSearchTables = {
            "DR Sandbox": "assay_test.lcb_dr",
            "DR": "assay.lcb_dr"
        }
        parent.searchTable_cb.addItems(self.saSearchTables.keys())

    def search(self):
        # Access parent widgets/data as needed
        sProject = self.parent.searchProject_cb.currentText()
        sTable = self.parent.searchTable_cb.currentText()
        selectedTable_key = self.parent.searchTable_cb.currentText()
        selectedTable_value = self.saSearchTables.get(selectedTable_key)
        print(selectedTable_value)
        df, lStatus = dbInterface.getDrData(self.parent.token, sProject, selectedTable_value)
        if not lStatus or df.empty:
            userInfo("No data found")
            return
        print('searching for data in project:', sProject, 'table:', selectedTable_value)
        # Populate the tableWidget with the DataFrame
        table = self.parent.drSearchResultTab  # Make sure this is your QTableWidget
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.astype(str))

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                value = str(df.iat[row, col])
                table.setItem(row, col, QTableWidgetItem(value))