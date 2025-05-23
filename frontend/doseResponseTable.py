from scipy.optimize import curve_fit
from scipy.integrate import quad
import os
import json
import math
import sys
import numpy as np
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QApplication, QFileDialog, QToolButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Font
from gradientDescent import fit_curve
import assaylib

import warnings
warnings.filterwarnings('ignore')

DERIVATIVE_TOP_CUTOFF = 17.0
DERIVATIVE_BOT_CUTOFF = 1.1
GRAPH_WIDTH = 400
GRAPH_HEIGHT = 300

# Define the 4-PL model function
def fourpl(x, slope, ic50, bottom, top):
    try:
        return bottom + (top - bottom) / (1 + (x / ic50)**slope)
    except:
        return -1

class ScatterplotWidget(QWidget):
    def __init__(self, data_dict, rowPosition, yScale, workingDir, parent=None):
        super(ScatterplotWidget, self).__init__(parent)
        self.rowPosition = rowPosition

        self.workingDirectory = workingDir

        self.figure = Figure(figsize=(3, 2), dpi=100) # dpi is optional, but good for consistency
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvas(self.figure)
        self.yScale = yScale
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        # self.data_dict contains the original data for each plot, so we can reconstruct the original curve at all times
        self.data_dict = data_dict
        # self.plotted_data contains the datapoints that are plotted (in case some points are de-selected in the GUI)
        self.plotted_data = data_dict
        self.confirmed = 'N'
        self.comment = ''
        slope, ic50, bottom, top, ic50_std, auc, sInfo = self.plot_scatter(data_dict, self.yScale)


    def resizeEvent(self, event):
        """
        Override resizeEvent to ensure plot redraws when widget size changes.
        This is crucial for Matplotlib integration.
        """
        super().resizeEvent(event)
        # It's good practice to call draw() here when the widget size changes
        # However, for FigureCanvas in a QTableWidget, the issue is often
        # more about the initial sizing and layout updates, not continuous redraw.
        # But this can help if the plot isn't scaling correctly on window resize etc.
        self.figure.tight_layout(pad=0.1)
        self.canvas.draw()


    def generateGraphString(self):
        template_string = f"""{{
  {{
    name='raw' style='dot' x_label='conc' x_unit='M'
    x_values={{{', '.join(map(str, self.x_values))}}}
    y_label='Inhibition'
    y_unit='%'
    y_values={{{', '.join(map(str, self.y_values))}}}
    y_error={{{', '.join(map(str, self.y_err_values))}}}
  }}{{
    name='fitsigmoidal' style='line' x_label='conc' x_unit='M'
    x_values={{{', '.join(map(str, self.x_values))}}}
    y_label='inhibition'
    y_unit='%'
    logic50={math.log10(self.ic50)}
    hillslope={self.slope}
    bottom={self.bottom}
    top={self.top}
  }}
}}"""
        return template_string


    def generateComment(self):
        comment = ''
        if abs(self.slope) > 4:
            comment += ' High Hill Slope;'
        if abs(self.slope) < 0.5:
            comment += ' Low Hill Slope;'
        if self.top < 80:
            comment += ' Ymax < 80%;'
            
        difference = self.top - self.bottom
        if difference < 50:
            comment += ' Low effect;'

        if self.derivative_ic50_div_bot < DERIVATIVE_BOT_CUTOFF:
            comment += ' No defined bottom;'

        if self.derivative_ic50_div_top < DERIVATIVE_TOP_CUTOFF:
            comment += ' No defined top;'
            
        return comment

    
    def isConfirmed(self):
        df = self.data_dict
        count_above_50 = df[df['inhibition'] > 50.0].shape[0]
        count_below_20 = df[df['inhibition'] < 20.0].shape[0]
        
        if count_below_20 > 0 and count_above_50 > 1 and (self.top - self.bottom > 50) and self.derivative_ic50_div_bot > DERIVATIVE_BOT_CUTOFF and self.derivative_ic50_div_top > DERIVATIVE_TOP_CUTOFF:
            self.confirmed = 'Y'
        else:
            self.confirmed = 'N'
        return self.confirmed


    def plot_scatter(self, df, yScale):
        self.ax.clear()
        self.plotted_data = df

        # Extract the 'x' and 'y' arrays
        self.x_values = np.array(df['finalConc_nM'].values/1000000000, dtype=np.float64)
        self.y_values = np.array(df['inhibition'].values, dtype=np.float64)
        self.y_err_values = np.array(df['yStd'].values, dtype=np.float64)
        sInfo = ''
        
        fitOk = True
        try:
            if 1 == 2:
                top = np.max(self.y_values)
                bottom = np.min(self.y_values)
                slope = -1
                ic50 = np.mean(self.x_values)/10
                bottom = 0
            
                # Fit the data to the 4-PL model
                max_top = 300
                min_top = 0
            
                max_bot = 60
                min_bot = -50
            
                max_slope = 30
                min_slope = -30

                max_ic50 = 0.01
                min_ic50 = 1e-12

                params, covariance = curve_fit(fourpl,
                                               self.x_values,
                                               self.y_values,
                                               maxfev = 100000,
                                               p0=[slope, ic50, bottom, top],
                                               bounds=([min_slope, min_ic50, min_bot, min_top], [max_slope, max_ic50, max_bot, max_top])
                                               )
                perr = np.sqrt(np.diag(covariance))
                slope_std, ic50_std, bottom_std, top_std = perr
                slope, ic50, bottom, top = params
                print(f'SciPy slope {slope} ic50 {ic50} bottom {bottom} top {top}')
                slope, ic50, bottom, top, sInfo, derivative_ic50_div_bot, derivative_ic50_div_top = fit_curve(self.x_values, self.y_values)
                print(f'Mats slope {slope} ic50 {ic50} bottom {bottom} top {top}')
            else:
                slope, ic50, bottom, top, sInfo, derivative_ic50_div_bot, derivative_ic50_div_top = fit_curve(self.x_values, self.y_values)
                # Extract the fitted parameters
                slope_std = ic50_std = bottom_std = top_std = -1
        except Exception as e:
            print(f'''Can't fit parameters {str(e)} {self.x_values[0]}''')
            fitOk = False
            slope = -1
            ic50 = -1
            bottom = -1
            top = -1
            ic50_std = -1

        # Generate a curve using the fitted parameters
        x_curve = np.logspace(np.log10(min(self.x_values)), np.log10(max(self.x_values)), 100)
        if fitOk == True:
            y_curve_fit = fourpl(x_curve, slope, ic50, bottom, top)

        # Plot the original data and the fitted curve with a logarithmic x-axis
        #plt.scatter(x_values, y_values, label='Original Data')

        self.ax.errorbar(self.x_values, self.y_values, yerr=self.y_err_values, fmt='o', label='Raw data')

        self.ax.set_ylim(min(min(self.y_values), 0) - 10, max(max(self.y_values), 100) + 10)
        
        if fitOk == True:
            self.ax.plot(x_curve, y_curve_fit, label='Fitted 4-PL Curve')
        if ic50 == -1:
            pass
        elif ic50 > 0.001:
            self.ax.axvline(ic50, color='r', linestyle='--', label=f'IC50 = {ic50:.2f} M')
        else:
            self.ax.axvline(ic50, color='r', linestyle='--', label=f'IC50 = {ic50*1e6:.2f} uM')
        self.ax.set_xscale('log')  # Set x-axis to logarithmic scale
        self.ax.set_xlabel('Concentration')
        self.ax.set_ylabel(yScale)

        # Create sub dir for images of the DR-curves (for Excel)
        imgDir = self.workingDirectory + '/img'
        
        # Check if the directory exists
        if not os.path.exists(imgDir):
            # If it doesn't exist, create it
            os.makedirs(imgDir)

        self.figure.tight_layout(pad=0.1) # New line            
        self.figure.savefig(f'{imgDir}/{self.rowPosition}.png', bbox_inches='tight', dpi=96)

        #self.figure.set_size_inches(5.81, 4.06)

        self.canvas.draw()

        (auc, err) = quad(fourpl, min(self.x_values), max(self.x_values), args=(slope, ic50, bottom, top))
        
        # Save all the parameters from the curve fitting
        self.auc = auc
        self.ic50 = ic50
        self.fit_quality = sInfo
        self.slope = -slope
        self.top = top
        self.bottom = bottom
        self.derivative_ic50_div_bot = derivative_ic50_div_bot
        self.derivative_ic50_div_top = derivative_ic50_div_top
        self.minConc = self.data_dict['finalConc_nM'].iloc[0]
        self.maxConc = self.data_dict['finalConc_nM'].iloc[-1]
        self.icmax = self.data_dict['inhibition'].iloc[-1]

        self.sGraph = self.generateGraphString()
        self.confirmed = self.isConfirmed()
        self.comment = self.generateComment()
        
        return slope, ic50, bottom, top, ic50_std, auc, sInfo


class DoseResponseTable(QTableWidget):
    def __init__(self, inputWidget):
        # What is the inputWidget, it has type QWidget ??????
        super(DoseResponseTable, self).__init__()
        self.ic50_col = 2
        self.ic50std_col = 3
        self.slope_col = 4
        self.bottom_col = 5
        self.top_col = 6
        self.minConc_col = 7
        self.maxConc_col = 8
        self.auc_col = 9
        self.icmax_col = 10
        self.graph_col = 11
        self.confirmed_col = 12
        self.comment_col = 13
        self.workingDirectory = ''
        self.parent = None

    def reset_table_data(self):
        """
        Resets the table by clearing all existing data and widgets,
        then optionally populates it with new_df.
        Ensures proper memory cleanup for embedded widgets.
        """
        
        # 1. Clear existing ScatterplotWidgets and ensure they are deleted
        num_rows = self.rowCount()
        for row in range(num_rows):
            widget_item = self.cellWidget(row, self.graph_col)
            if isinstance(widget_item, ScatterplotWidget):
                # Remove the widget from the cell
                self.removeCellWidget(row, self.graph_col)
                # Schedule the widget for deletion. This is CRUCIAL for memory cleanup.
                widget_item.deleteLater()
                # print(f"  - Scheduled ScatterplotWidget in row {row} for deletion.")

        # 2. Clear all table contents and reset row count
        self.clearContents() # Clears text in cells
        self.setRowCount(0)   # Resets the number of rows

        print("Existing table data and widgets cleared.")

    
    def qtablewidget_to_dataframe(self):
        """
        Converts a QTableWidget to a pandas DataFrame.
        
        Args:
        table_widget (QTableWidget): The QTableWidget to convert.
        
        Returns:
        pd.DataFrame: A pandas DataFrame containing the QTableWidget data.
        """
        
        data = []
        headers = []

        # Get headers
        for column in range(self.columnCount()):
            headers.append(self.horizontalHeaderItem(column).text())
        headers.append('comment')

        # Get data
        for row in range(self.rowCount()):

            row_data = []
            sComment = ''
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append(None)  # Handle empty cells
                
            row_data.append(sComment)
            data.append(row_data)
            
        df = pd.DataFrame(data, columns=headers)
        #df = self.generateComment(df)

        '''
        mask = ~df['Compound'].str.startswith('CBK')
        # Remove the rows that doesn't start with 'CBK'
        df = df[~mask]
        '''
        return df

        
    def generate_scatterplots(self, file_path, yScale, parent):
        self.parent = parent
        outputDir = os.path.dirname(file_path)
        self.workingDirectory = outputDir
        # Set the graph column to be 600 wide

        self.reset_table_data()
        #self.clearContents()
        #self.setRowCount(0)

        
        self.setColumnWidth(self.graph_col, GRAPH_WIDTH)
        df = pd.read_excel(file_path)
        df = df[df['Compound ID'].str.startswith('CBK')] # Remove all controls

        dialog = assaylib.CancelDialog(self)
        dialog.show()

        iTotPlotNum = len(df.groupby('Batch nr'))
        iCount = 0
        for batch_nr, batch_df in df.groupby('Batch nr'):
            iCount += 1
            dialog.update_label(f"{iCount + 1} of {iTotPlotNum} curves")
            if dialog.cancelled:
                break
            
            rowPosition = self.rowCount()
            if parent.test == 'true':
                if rowPosition > 20:
                    continue
            self.insertRow(rowPosition)
            self.setRowHeight(rowPosition, GRAPH_HEIGHT)
            
            print(f'Plot nr: {rowPosition}')
            # Call the scatter function for each batch
            self.plotCurve(batch_df, rowPosition, yScale)

        dialog.close()
        self.saveToExcel('DR_Excel.xlsx')
        return batch_df


    def changeIC50_EC50_heading(self, newHeading):
        header_item = self.horizontalHeaderItem(self.ic50_col)
        print(newHeading)
        if header_item:
            header_item.setText(newHeading)


    def plotCurve(self, batch_df, rowPosition, yScale):
        # "Batch nr" "Compound ID" "finalConc_nM" "yMean" "yStd"
        batch = batch_df['Batch nr'].iloc[0]
        compound = batch_df['Compound ID'].iloc[0]

        scatterplot_widget = ScatterplotWidget(batch_df, rowPosition, yScale, self.workingDirectory)
        item = QTableWidgetItem(batch)
        self.setItem(rowPosition, 0, item)

        item = QTableWidgetItem(compound)
        self.setItem(rowPosition, 1, item)

        self.org_figsize = scatterplot_widget.figure.get_size_inches()
        
        item = QTableWidgetItem()
        self.setItem(rowPosition, self.graph_col, item)
        self.setCellWidget(rowPosition, self.graph_col, scatterplot_widget)
        self.setCurrentCell(rowPosition, self.graph_col)
        self.updateTable(rowPosition, scatterplot_widget)

        QApplication.processEvents()

    def updateMaxConc(self, row, maxConc):
        item = QTableWidgetItem(str(f"{maxConc:.1f}"))
        self.setItem(row, self.maxConc_col, item)
        ### Mats
        ### On next line we need to find the inhibition for the higest concentration when we have deselected concs.
        # self.setItem(row, self.icmax_col, item)


    def updateTable(self, rowPosition, scatterplot_widget):
        
        item = QTableWidgetItem(str("{:.2e}".format(scatterplot_widget.ic50)))
        self.setItem(rowPosition, self.ic50_col, item) # 2

        #item = QTableWidgetItem(str("{:.2e}".format(scatterplot_widget.ic50_std)))
        item = QTableWidgetItem(scatterplot_widget.fit_quality)
        self.setItem(rowPosition, self.ic50std_col, item) # 3

        item = QTableWidgetItem(str(f"{scatterplot_widget.slope:.2f}"))
        self.setItem(rowPosition, self.slope_col, item) #4

        item = QTableWidgetItem(str(f"{scatterplot_widget.bottom:.2f}"))
        self.setItem(rowPosition, self.bottom_col, item) # 5

        item = QTableWidgetItem(str(f"{scatterplot_widget.top:.2f}"))
        self.setItem(rowPosition, self.top_col, item)

        item = QTableWidgetItem(str(f"{scatterplot_widget.minConc:.1f}"))
        self.setItem(rowPosition, self.minConc_col, item)

        item = QTableWidgetItem(str(f"{scatterplot_widget.maxConc:.1f}"))
        self.setItem(rowPosition, self.maxConc_col, item)

        item = QTableWidgetItem(str(f"{scatterplot_widget.icmax:.2f}"))
        self.setItem(rowPosition, self.icmax_col, item)

        item = QTableWidgetItem(str(f"{scatterplot_widget.auc:.5f}"))
        self.setItem(rowPosition, self.auc_col, item)

        item = QTableWidgetItem(str(f"{scatterplot_widget.confirmed}"))
        self.setItem(rowPosition, self.confirmed_col, item)

        item = QTableWidgetItem(str(f"{scatterplot_widget.comment}"))
        self.setItem(rowPosition, self.comment_col, item)


    def saveToExcel(self, sFileName = None):
        sDir = self.workingDirectory
        sFile = 'DR_Excel.xlsx'
        file_path = os.path.join(sDir, sFile)

        imgDir = self.workingDirectory + '/img'
        if not os.path.exists(imgDir):
            # Create the directory and any missing parent directories
            os.makedirs(imgDir)
        
        if sFileName in (None, False):
            sDefaultFile = os.path.join(sDir, sFile)
            # Open a file dialog to select the location and file name for saving
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "Save As", sDefaultFile,
                                                       "Excel Files (*.xlsx *.xls)",
                                                       options=options)

            file_path = file_name
            if file_name in ('', None):
                return
            sDir = os.path.dirname(file_name)

            #imgDir = sDir + '/img'
            if not os.path.exists(imgDir):
                # Create the directory and any missing parent directories
                os.makedirs(imgDir)

        wb = Workbook()
        ws = wb.active

        headings = ["Batch", "Compound", "IC50", "Fit quality", "Slope",
                    "Bottom", "Top", "MinConc nM", "MaxConc nM", "AUC", "ICMax", "Graph", "Confirmed", "Comment"]
                
        # Convert QTableWidget data to a pandas DataFrame
        table_data = []
        for row in range(self.rowCount()):
            row_data = [self.item(row, col).text() if col < len(headings) else None for col in range(self.columnCount())]
            table_data.append(row_data)


        df = pd.DataFrame(table_data, columns=headings)

        for col_num, heading in enumerate(headings, 1):
            cell = ws.cell(row=1, column=col_num, value=heading)
            cell.font = Font(bold=True)

        # Write DataFrame to Excel
        for r_idx, row in enumerate(df.itertuples(index=False), start=2):  # Start from row 2 to leave space for header
            for c_idx, value in enumerate(row, start=1):
                if c_idx > 2:
                    try:
                        if c_idx in (3, 4):
                            ws.cell(row=r_idx, column=c_idx, value=float(f'{value:e}'))
                        else:
                            ws.cell(row=r_idx, column=c_idx, value=float(value))
                    except:
                        ws.cell(row=r_idx, column=c_idx, value=value)
                else:
                    ws.cell(row=r_idx, column=c_idx, value=value)

        # Add scatterplots to Excel
        for i, canvas in enumerate(df['Graph']):
            image_path = f"{imgDir}/{i}.png"
            img = Image(image_path)
                        
            #ws.add_image(img)
            ws.add_image(img, f"L{i + 2}")

        # Adjust row heights and column widths to fit images
        for r_idx in range(2, len(df) + 2):  # Include header row
            ws.row_dimensions[r_idx].height = 160  # Adjust the height as needed
            
        for c_idx in range(1, len(headings) + 1):
            ws.column_dimensions[chr(ord('A') + c_idx - 1)].width = 13  # Adjust the width as needed

        ws.column_dimensions[chr(ord('L'))].width = 40
        
        # Save the Excel workbook
        wb.save(file_path)
        self.parent.saveExcel_btn.setEnabled(False)

        try:
            if self.parent.finalPreparedDR['deselected'].any():
                # There are rows where 'deselected' is True
                # Save the new dataframe without the deselected datapoints
                df_filtered = self.parent.finalPreparedDR[self.parent.finalPreparedDR['deselected'] == False]
                df_filtered = df_filtered.drop(columns=['deselected'])
                df_filtered.to_excel(self.parent.pathToFinalPreparedDR_deselects, index=False)
        except:
            # There where no deselected items
            pass
