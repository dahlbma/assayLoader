from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
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

        #self.data = {'x': np.random.rand(100), 'y': np.random.rand(100), 'label': [f'Data {i+1}' for i in range(100)]}
        #self.scatter = self.ax.scatter(self.data['x'], self.data['y'], picker=True)
        self.ax.set_xlabel('X-axis')
        self.ax.set_ylabel('Y-axis')

        mplcursors.cursor(hover=True).connect("add", self.show_data)

        self.setWindowTitle('Scatter Plot Window')

    def show_data(self, df):
        self.df = df
        self.data = {'x': self.df.index, 'y': df['inhibition'], 'label': [f'Data {self.df.index}']}
        self.scatter = self.ax.scatter(self.df.index, self.df['inhibition'], picker=True)

        index = self.df.index
        x_val = self.df.index[index]
        y_val = self.df['inhibition'][index]
        #label = self.data['label'][index]

        #tooltip_text = f'{label}\nX: {x_val:.2f}\nY: {y_val:.2f}'

        #self.annotation.set_text(tooltip_text)
        #self.annotation.get_bbox_patch().set_facecolor('white')
        #self.annotation.get_bbox_patch().set_alpha(0.7)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.canvas.setGeometry(0, self.toolbar.height(), self.width(), self.height() - self.toolbar.height())

