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
import configParams as cfg


def parse_graph_column(graph_str):
    # Extract x_values, y_values, y_error from the 'raw' section
    try:
        raw_match = re.search(r"\{name='raw'.*?x_values=\{([^\}]*)\}.*?y_values=\{([^\}]*)\}.*?y_error=\{([^\}]*)\}", graph_str, re.DOTALL)
        fit_match = re.search(r"\{name='fitsigmoidal'.*?logic50=([-\d\.]+) hillslope=([-\d\.]+) bottom=([-\d\.]+) top=([-\d\.]+)", graph_str, re.DOTALL)
        if not raw_match or not fit_match:
            return None

        x_values = [float(x) for x in raw_match.group(1).split(',')]
        y_values = [float(y) for y in raw_match.group(2).split(',')]
        y_error_raw = raw_match.group(3).split(',')
        try:
            y_error = [float(e) for e in y_error_raw]
        except Exception:
            # If any conversion fails, set y_error to all zeros of same length
            y_error = [0.0 for _ in y_error_raw]

        logic50 = float(fit_match.group(1))
        hillslope = float(fit_match.group(2))
        bottom = float(fit_match.group(3))
        top = float(fit_match.group(4))
        ic50 = 10 ** logic50
        return x_values, y_values, y_error, ic50, -hillslope, bottom, top
    except Exception as e:
        printDbg(f"Error parsing graph column: {e}")
        printDbg(graph_str)
        return None


def four_parameter_logistic(x, slope, ic50, bottom, top):
    return bottom + (top - bottom) / (1 + (x / ic50) ** -slope)


class DrSearch:
    def clear_table(self):
        """Remove all rows and clean up embedded widgets in the drSearchResultTab table."""
        table = self.parent.drSearchResultTab
        # Remove and delete all cell widgets to avoid memory leaks
        row_count = table.rowCount()
        col_count = table.columnCount()
        # Remove widgets row by row from bottom to top to avoid shifting issues
        for row in reversed(range(row_count)):
            for col in range(col_count):
                widget = table.cellWidget(row, col)
                if widget is not None:
                    table.removeCellWidget(row, col)
                    widget.deleteLater()
        # Remove all items (QTableWidgetItem) as well
        for row in reversed(range(row_count)):
            for col in range(col_count):
                item = table.item(row, col)
                if item is not None:
                    table.takeItem(row, col)
        table.clearContents()
        table.setRowCount(0)
        table.viewport().update()  # Force a repaint of the table
        QApplication.processEvents()

    def __init__(self, parent):
        self.parent = parent  # Reference to DoseResponseScreen or needed context
        self.saSearchTables = cfg.searchTables
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
        selectedTable_key = sTable
        selectedTable_value = self.saSearchTables.get(selectedTable_key)
        printDbg(selectedTable_value)
        df, lStatus = dbInterface.getDrData(self.parent.token, sProject, selectedTable_value)
        if not lStatus or df.empty:
            userInfo("No data found")
            return

        # Clear the table before populating
        self.clear_table()

        # Populate the tableWidget with the DataFrame
        table = self.parent.drSearchResultTab  # Make sure this is your QTableWidget
        table.setRowCount(0)
        QApplication.processEvents()
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.astype(str))

        table.setSortingEnabled(True)

        # First, populate all rows and columns except the plot
        graph_col_index = df.columns.get_loc('graph')
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                if col == graph_col_index:
                    continue
                item = QTableWidgetItem(str(df.iat[row, col]))
                table.setItem(row, col, item)

        # Then, generate and insert the plots for each row
        for row in range(df.shape[0]):
            graph_str = df.iloc[row]['graph']
            parsed = parse_graph_column(graph_str)
            if parsed is None:
                continue  # or handle error
            x_values, y_values, y_error, ic50, hillslope, bottom, top = parsed
            data_dict = {
                'finalConc_nM': np.array(x_values) * 1e9,
                'inhibition': np.array(y_values),
                'yStd': np.array(y_error)
            }
            df_tmp = pd.DataFrame(data_dict)
            df_tmp['Batch nr'] = "1"
            df_tmp['Compound ID'] = "2"
            df_tmp = df_tmp[['Batch nr', 'Compound ID', 'finalConc_nM', 'yStd', 'inhibition']]

            working_dir = self.parent.workingDirectory if hasattr(self.parent, 'workingDirectory') and self.parent.workingDirectory else os.path.join(os.getcwd(), 'img')
            if not os.path.exists(working_dir):
                os.makedirs(working_dir, exist_ok=True)
            scatterplot_widget = ScatterplotWidget(df_tmp, row, 'Inhibition (%)', working_dir)
            scatterplot_widget.set_data(hillslope, ic50, bottom, top, x_values, y_values, y_error)
            createExcel = False
            scatterplot_widget.plot_curve(createExcel)
            table.setColumnWidth(graph_col_index, cfg.GRAPH_WIDTH)
            table.setRowHeight(row, cfg.GRAPH_HEIGHT)
            table.setCellWidget(row, graph_col_index, scatterplot_widget)
            QApplication.processEvents()