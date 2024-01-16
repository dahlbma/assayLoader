from scipy.optimize import curve_fit
import os
import json
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


# Define the 4-PL model function
def fourpl(x, slope, ic50, bottom, top):
    return bottom + (top - bottom) / (1 + (x / ic50)**slope)

file_path = "Dose_response_Query.csv"

class ScatterplotWidget(QWidget):
    def __init__(self, data_dict, parent=None):
        super(ScatterplotWidget, self).__init__(parent)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        #self.canvas.setSizePolicy(QVBoxLayout.Expanding, QVBoxLayout.Expanding)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.plot_scatter(data_dict)

    def plot_scatter(self, data_dict):

        # Extract the 'x' and 'y' arrays
        x_values = np.array(data_dict.get('x', []), dtype=np.float64)
        y_values = np.array(data_dict.get('y', []), dtype=np.float64)
        y_err_values = np.array(data_dict['yErr'], dtype=np.float64)
        
        print('############################')
        try:
            oldHillParams = data_dict.get('Hill', [])
        except:
            print(f'Failed with old Hill values')
            print(data_dict)
            return -1
        oldBottom = oldHillParams['bottom']
        oldTop = oldHillParams['top']
        oldSlope = oldHillParams['slope']
        oldIC50 = oldHillParams['IC50']
        print(data_dict.get('Hill', []))
        #print(oldBottom)
        fitOk = True
        try:
            top = np.max(y_values)
            bottom = np.min(y_values)
            slope = 1
            ic50 = np.mean(x_values)*2
            top = 100
            bottom = 0
            # Fit the data to the 4-PL model
            params, covariance = curve_fit(fourpl, x_values, y_values, maxfev = 100000, p0=[slope, ic50, bottom, top])
            #print(f'covariance: {covariance}')
            # Extract the fitted parameters
            slope, ic50, bottom, top = params
        except Exception as e:
            print(f'''Can't fit parameters {str(e)}''')
            fitOk = False
            slope = -1
            ic50 = -1
            bottom = -1
            top = -1

        # Generate a curve using the fitted parameters
        x_curve = np.logspace(np.log10(min(x_values)), np.log10(max(x_values)), 100)
        if fitOk == True:
            y_curve_fit = fourpl(x_curve, slope, ic50, bottom, top)
        else:
            y_curve_fit = fourpl(x_curve, oldSlope, oldIC50, oldTop, oldBottom)
        y_old_fit = fourpl(x_curve, oldSlope, oldIC50, oldTop, oldBottom)

        # Plot the original data and the fitted curve with a logarithmic x-axis
        #plt.scatter(x_values, y_values, label='Original Data')

        plt.errorbar(x_values, y_values, yerr=y_err_values, fmt='o', label='Raw data')

        plt.plot(x_curve, y_curve_fit, label='Fitted 4-PL Curve')
        plt.plot(x_curve, y_old_fit, label='Old Fitted 4-PL Curve')
        if ic50 == -1:
            plt.axvline(oldIC50, color='r', linestyle='--', label=f'IC50 = Failed')
            plt.axvline(oldIC50, color='g', linestyle='--', label=f'Old IC50 = {oldIC50:.2f} M')
        elif ic50 > 0.001:
            plt.axvline(ic50, color='r', linestyle='--', label=f'IC50 = {ic50:.2f} M')
            plt.axvline(oldIC50, color='g', linestyle='--', label=f'Old IC50 = {oldIC50:.2f} M')
        else:
            plt.axvline(ic50, color='r', linestyle='--', label=f'IC50 = {ic50*1e6:.2f} uM')
            plt.axvline(oldIC50, color='g', linestyle='--', label=f'Old IC50 = {oldIC50*1e6:.2f} uM')
        plt.xscale('log')  # Set x-axis to logarithmic scale
        plt.xlabel('Concentration')
        plt.ylabel('Response')
        plt.legend()
        # Print the fitted parameters, Hill slope, and IC50
        #print(f"Fitted Parameters: a={a_fit:.4f}, b={b_fit:.4f}, c={c_fit:.4f}, d={d_fit:.4f}")
        #print(f"IC50: {ic50:.2e}")
        self.canvas.draw()
        return 1


class ScatterplotsTable(QMainWindow):
    def __init__(self):
        super(ScatterplotsTable, self).__init__()

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.table_widget = QTableWidget(self.central_widget)
        self.table_widget.setRowCount(200)
        self.table_widget.setColumnCount(1)

        # Set row height to 600 pixels
        for i in range(200):
            self.table_widget.setRowHeight(i, 600)

        # Set column width to 800 pixels
        self.table_widget.setColumnWidth(0, 800)

        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.table_widget)

        self.generate_scatterplots()

    def generate_scatterplots(self):
        with open(file_path, 'r') as file:
            # Read the file line by line
            for line_number, line in enumerate(file, start=1):
                print(line_number)
                # Parse the line as JSON
                try:
                    data_dict = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in line {line_number}: {e}")
                    continue
                try:
                    scatterplot_widget = ScatterplotWidget(data_dict)
                except:
                    continue
                
                item = QTableWidgetItem()
                item.setSizeHint(scatterplot_widget.sizeHint())
                self.table_widget.setItem(line_number, 0, item)
                self.table_widget.setCellWidget(line_number, 0, scatterplot_widget)

                if line_number > 200:
                    return

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScatterplotsTable()
    window.setGeometry(100, 100, 350, 1000)  # Adjust window width and height
    window.show()
    sys.exit(app.exec_())
