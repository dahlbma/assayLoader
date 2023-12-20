import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import mplcursors
import numpy as np

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

        self.data = {'x': np.random.rand(100), 'y': np.random.rand(100), 'label': [f'Data {i+1}' for i in range(100)]}
        self.scatter = self.ax.scatter(self.data['x'], self.data['y'], picker=True)
        self.ax.set_xlabel('X-axis')
        self.ax.set_ylabel('Y-axis')

        mplcursors.cursor(hover=True).connect("add", self.show_data)

        self.setWindowTitle('Scatter Plot Window')

    def show_data(self, sel):
        index = sel.index
        print(index)
        x_val = self.data['x'][index]
        y_val = self.data['y'][index]
        label = self.data['label'][index]

        tooltip_text = f'{label}\nX: {x_val:.2f}\nY: {y_val:.2f}'

        sel.annotation.set_text(tooltip_text)
        sel.annotation.get_bbox_patch().set_facecolor('white')
        sel.annotation.get_bbox_patch().set_alpha(0.7)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.canvas.setGeometry(0, self.toolbar.height(), self.width(), self.height() - self.toolbar.height())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.button = QPushButton('Show Scatter Plot', self)
        self.button.clicked.connect(self.show_scatter_plot)

        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.button)

        self.setGeometry(100, 100, 400, 200)
        self.setWindowTitle('Main Window')

    def show_scatter_plot(self):
        scatter_window = ScatterPlotWindow(self)
        scatter_window.setGeometry(200, 200, 600, 400)
        scatter_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
