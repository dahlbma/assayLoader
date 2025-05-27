from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import mplcursors
import pandas as pd

class ScatterPlotWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.ax.set_xlabel('Data point')
        self.ax.set_ylabel('Inhibition')

        self.setWindowTitle('Inhibition')


    def show_data(self, df, hitLimit):
        self.df = df

        # Create a scatterplot of the "inhibition" columns
        self.ax.scatter(range(len(df)), df['posCtrlInhibition'], label='PosCtrl', marker='.', s=30, c='green')
        self.ax.scatter(range(len(df)), df['inhibition'], label='Inhibition', marker='.', s=30, c='blue')
        self.ax.scatter(range(len(df)), df['negCtrlInhibition'], label='NegCtrl', marker='.', s=30, c='red')
        # Draw a horizontal line at the hit limit
        self.ax.axhline(y=hitLimit, color='red', linestyle='--', label='Hit Limit')
        mplcursors.cursor(hover=True).connect("add", self.show_tooltip)
        

    def show_tooltip(self, sel):
        index = sel.index
        x_val = index
        try:
            if pd.isna(self.df['inhibition'][index]):
                if pd.isna(self.df['negCtrlInhibition'][index]):
                    if pd.isna(self.df['posCtrlInhibition'][index]):
                        y_val = 'Fix me'
                    else:
                        y_val = self.df['posCtrlInhibition'][index]
                else:
                    y_val = self.df['negCtrlInhibition'][index]
            else:
                y_val = self.df['inhibition'][index]

        except:
            # We hit the inhibition line, just return
            return

        pd.isna(y_val)
        plate = self.df['plate'][index]
        well = self.df['well'][index]
        compound_id = self.df['compound_id'][index]
        tooltip_text = f'{plate} {well}\nCmp: {compound_id}\nInhibition: {y_val:.2f}'

        sel.annotation.set_text(tooltip_text)
        sel.annotation.get_bbox_patch().set_facecolor('white')
        sel.annotation.get_bbox_patch().set_alpha(0.9)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.canvas.setGeometry(0, self.toolbar.height(), self.width(), self.height() - self.toolbar.height())

