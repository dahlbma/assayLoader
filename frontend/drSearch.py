import re, sys, os, logging, csv
from PyQt5.uic import loadUi
#from PyQt5.QtCore import QRegExp, QDate, Qt
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QComboBox, QDialog, QPushButton, QApplication
#from PyQt5.QtWidgets import QCheckBox, QSpacerItem, QSizePolicy, QMessageBox
import openpyxl
from pathlib import Path
import pandas as pd
from assaylib import *
from prepareHarmonyFile import *
from prepareEnvisionFile import *
from selectDataColumn import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from scatterplotWidget import ScatterplotWidget


def parse_graph_column(graph_str):
    # Extract x_values, y_values, y_error from the 'raw' section
    raw_match = re.search(r"\{name='raw'.*?x_values=\{([^\}]*)\}.*?y_values=\{([^\}]*)\}.*?y_error=\{([^\}]*)\}", graph_str, re.DOTALL)
    fit_match = re.search(r"\{name='fitsigmoidal'.*?logic50=([-\d\.]+) hillslope=([-\d\.]+) bottom=([-\d\.]+) top=([-\d\.]+)", graph_str, re.DOTALL)
    if not raw_match or not fit_match:
        return None

    x_values = [float(x) for x in raw_match.group(1).split(',')]
    y_values = [float(y) for y in raw_match.group(2).split(',')]
    y_error = [float(e) for e in raw_match.group(3).split(',')]

    logic50 = float(fit_match.group(1))
    hillslope = float(fit_match.group(2))
    bottom = float(fit_match.group(3))
    top = float(fit_match.group(4))

    return x_values, y_values, y_error, logic50, hillslope, bottom, top

def four_parameter_logistic(x, slope, ic50, bottom, top):
    return bottom + (top - bottom) / (1 + (x / ic50) ** -slope)


class DrSearch:
    def __init__(self, parent):
        self.parent = parent  # Reference to DoseResponseScreen or needed context
        self.saSearchTables = {
            "DR Sandbox": "assay_test.lcb_dr",
            "DR": "assay.lcb_dr"
        }
        parent.searchTable_cb.addItems(self.saSearchTables.keys())

    def show_plot_in_widget(self, x_values, y_values, y_error, hillslope, ic50, bottom, top):
        # Remove any previous plot
        for i in reversed(range(self.parent.plotWidget.layout().count())):
            widgetToRemove = self.parent.plotWidget.layout().itemAt(i).widget()
            self.parent.plotWidget.layout().removeWidget(widgetToRemove)
            widgetToRemove.setParent(None)

        # Create a new Figure and Canvas
        fig = Figure(figsize=(7, 5))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.errorbar(x_values, y_values, yerr=y_error, fmt='o', label='Raw data')
        x_fit = np.logspace(np.log10(min(x_values)), np.log10(max(x_values)), 100)
        y_fit = four_parameter_logistic(x_fit, hillslope, ic50, bottom, top)
        ax.plot(x_fit, y_fit, label='4PL fit')
        ax.set_xscale('log')
        ax.set_xlabel('Concentration (M)')
        ax.set_ylabel('Inhibition (%)')
        ax.set_title('Dose-Response Curve')
        ax.legend()

        # Add the canvas to the plotWidget's layout
        self.parent.plotWidget.layout().addWidget(canvas)


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
            # Prepare a data_dict similar to what ScatterplotWidget expects
            # You may need to adapt this if your DataFrame columns differ
            graph_str = df.iloc[row]['graph']
            parsed = parse_graph_column(graph_str)
            if parsed is None:
                continue  # or handle error
            x_values, y_values, y_error, logic50, hillslope, bottom, top = parsed
            data_dict = {
                'finalConc_nM': np.array(x_values) * 1e9,  # convert M to nM if needed
                'inhibition': np.array(y_values),
                'yStd': np.array(y_error)
            }            # You may need to parse these arrays from the 'graph' column if they are stored as strings

            df_tmp = pd.DataFrame(data_dict)
            # Add the extra columns
            df_tmp['Batch nr'] = "1"
            df_tmp['Compound ID'] = "2"
            # Reorder columns as desired
            df_tmp = df_tmp[['Batch nr', 'Compound ID', 'finalConc_nM', 'yStd', 'inhibition']]

            # Create the plot widget
            scatterplot_widget = ScatterplotWidget(df_tmp, row, 'Inhibition (%)', self.parent.workingDirectory)
            # Insert the widget into the last column
            table.setCellWidget(row, df.shape[1], scatterplot_widget)
            QApplication.processEvents()
            print(f"Row {row} processed with ScatterplotWidget")
            # Optionally, fill in the rest of the columns with data
            for col in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iat[row, col]))
                table.setItem(row, col, item)