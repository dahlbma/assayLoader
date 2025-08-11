import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from scipy.optimize import curve_fit
from scipy.integrate import quad
import math
from gradientDescent import fit_curve
#from assaylib import fit_curve, fourpl

DERIVATIVE_TOP_CUTOFF = 17.0
DERIVATIVE_BOT_CUTOFF = 1.1

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
        self.confirmed = 'N'
        self.comment = ''

        self.slope = None
        self.ic50 = None
        self.bottom = None
        self.top = None
        self.ic50_std = None
        self.auc = None
        self.sInfo = None

    def set_data(self, hillslope, ic50, bottom, top, x_values, y_values, y_error):
        """
        Set the data for the scatter plot and fit curve.
        This method is called to update the plot with new data.
        """

        self.slope = hillslope
        self.ic50 = ic50
        self.bottom = bottom
        self.top = top
        self.fitOk = True
        self.x_values = x_values
        self.y_values = y_values
        self.y_err_values = y_error
        

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
        if not hasattr(self, "derivative_ic50_div_bot"):
            return ''
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
        if not hasattr(self, "derivative_ic50_div_bot"):
            return ''
        df = self.data_dict
        count_above_50 = df[df['inhibition'] > 50.0].shape[0]
        count_below_20 = df[df['inhibition'] < 20.0].shape[0]
        
        if count_below_20 > 0 and count_above_50 > 1 and (self.top - self.bottom > 50) and self.derivative_ic50_div_bot > DERIVATIVE_BOT_CUTOFF and self.derivative_ic50_div_top > DERIVATIVE_TOP_CUTOFF:
            self.confirmed = 'Y'
        else:
            self.confirmed = 'N'
        return self.confirmed


    def fit_curve_to_data(self, data_dict = None, yScale = None):
        if data_dict is None:
            data_dict = self.data_dict
        if yScale is None:
            yScale = self.yScale

        self.ax.clear()
        # Extract the 'x' and 'y' arrays
        self.x_values = np.array(data_dict['finalConc_nM'].values/1000000000, dtype=np.float64)
        self.y_values = np.array(data_dict['inhibition'].values, dtype=np.float64)
        self.y_err_values = np.array(data_dict['yStd'].values, dtype=np.float64)
        sInfo = ''
        
        self.fitOk = True
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
                self.slope_std, self.ic50_std, self.bottom_std, self.top_std = perr
                self.slope, self.ic50, self.bottom, self.top = params
                print(f'SciPy slope {self.slope} ic50 {self.ic50} bottom {self.bottom} top {self.top}')
                (self.slope, self.ic50,
                 self.bottom, self.top,
                 self.sInfo, self.derivative_ic50_div_bot,
                 self.derivative_ic50_div_top) = fit_curve(self.x_values, self.y_values)
                print(f'Mats slope {self.slope} ic50 {self.ic50} bottom {self.bottom} top {self.top}')
            else:
                (self.slope, self.ic50,
                 self.bottom, self.top,
                 self.sInfo, self.derivative_ic50_div_bot,
                 self.derivative_ic50_div_top) = fit_curve(self.x_values, self.y_values)
                # Extract the fitted parameters
                self.slope_std = self.ic50_std = self.bottom_std = self.top_std = -1
                self.plot_curve(createExcel = False)
        except Exception as e:
            print(f'''Can't fit parameters {str(e)} {self.x_values[0]}''')
            self.fitOk = False
            self.slope = -1
            self.ic50 = -1
            self.bottom = -1
            self.top = -1
            self.ic50_std = -1

    def plot_curve(self, createExcel = True):
        # Generate a curve using the fitted parameters
        x_curve = np.logspace(np.log10(min(self.x_values)), np.log10(max(self.x_values)), 40)  # Reduced from 100 to 40 points
        if self.fitOk == True:
            y_curve_fit = fourpl(x_curve, self.slope, self.ic50, self.bottom, self.top)

        self.ax.errorbar(self.x_values, self.y_values, yerr=self.y_err_values, fmt='o', color='blue', label='Raw data')

        self.ax.set_ylim(min(min(self.y_values), 0) - 10, max(max(self.y_values), 100) + 10)

        if self.fitOk == True:
            self.ax.plot(x_curve, y_curve_fit, color='orange', label='Fitted 4-PL Curve')

        if self.ic50 == -1:
            pass
        elif self.ic50 > 0.001:
            self.ax.axvline(self.ic50, color='r', linestyle='--', label=f'IC50 = {self.ic50:.2f} M')
        else:
            self.ax.axvline(self.ic50, color='r', linestyle='--', label=f'IC50 = {self.ic50*1e6:.2f} uM')
        self.ax.set_xscale('log')  # Set x-axis to logarithmic scale
        self.ax.set_xlabel('Concentration')
        self.ax.set_ylabel(self.yScale)

        # Only create image directory and save figure if exporting for Excel
        if createExcel:
            imgDir = self.workingDirectory + '/img'
            if not os.path.exists(imgDir):
                os.makedirs(imgDir)
            self.figure.tight_layout(pad=0.1)
            self.figure.savefig(f'{imgDir}/{self.rowPosition}.png', bbox_inches='tight', dpi=96)

        self.canvas.draw()

        (auc, err) = quad(fourpl, min(self.x_values), max(self.x_values), args=(self.slope, self.ic50, self.bottom, self.top))

        # Save all the parameters from the curve fitting
        self.auc = auc

        self.minConc = self.data_dict['finalConc_nM'].iloc[0]
        self.maxConc = self.data_dict['finalConc_nM'].iloc[-1]
        self.icmax = self.data_dict['inhibition'].iloc[-1]

        self.sGraph = self.generateGraphString()
        self.confirmed = self.isConfirmed()
        self.comment = self.generateComment()

        return self.slope, self.ic50, self.bottom, self.top, self.ic50_std, self.auc, self.sInfo
