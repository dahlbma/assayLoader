import sys, requests, json, os, subprocess, platform, logging, dbInterface, re, shutil
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidget, QTableWidgetItem, QWidget
from PyQt5.QtWidgets import QProgressBar, QVBoxLayout, QDialog, QLabel, QDialogButtonBox, QPushButton, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot

def gotoSP(self):
    resize_window(self)
    self.window().setCurrentIndex(1)
    self.window().widget(1).instrument_cb.setFocus()
    return

def gotoDR(self):
    resize_window(self)
    self.window().setCurrentIndex(2)
    #self.window().widget(2).drPlateIdFile_btn.setFocus()
    return


def delete_all_files_in_directory(directory_path):
    # Check if the directory exists
    if os.path.exists(directory_path):
        # Iterate over all the files in the directory
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                # Check if it's a file and delete it
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                # If it's a directory, remove it too
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    else:
        print(f'The directory {directory_path} does not exist')


class Worker(QObject):
    finished = pyqtSignal()
    intReady = pyqtSignal(int)

    @pyqtSlot()
    def proc_counter(self, i = 1):
        if i < 100:
            self.intReady.emit(i)
        else:
            self.finished.emit()

class PopUpProgress(QWidget):

    def __init__(self, sHeader = ""):
        super().__init__()
        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 500, 75)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.pbar)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 550, 100)
        self.setWindowTitle(sHeader)
        self.pbar.show()

        self.thread = QtCore.QThread()
        self.obj = Worker()
        self.obj.intReady.connect(self.on_count_changed)
        self.obj.moveToThread(self.thread)
        self.obj.finished.connect(self.thread.quit)
        self.thread.started.connect(self.obj.proc_counter)
        self.thread.start()

    def on_count_changed(self, value):
        self.pbar.setValue(value)

def send_msg(title, text, icon=QMessageBox.Information, e=None):
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setIcon(icon)
    msg.setText(text)
    clipboard = QApplication.clipboard()
    if e is not None:
        #add clipboard btn
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Save)
        buttonS = msg.button(QMessageBox.Save)
        buttonS.setText('Save to clipboard')
    msg.exec_()
    if e is not None:
        if msg.clickedButton() == buttonS:
            #copy to clipboard if clipboard button was clicked
            clipboard.setText(text)
            cb_msg = QMessageBox()
            cb_msg.setText(clipboard.text()+" \n\ncopied to clipboard!")
            cb_msg.exec_()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def resize_window(self, height=800, width=1200):
    desktop = QApplication.desktop()

    windowHeight = int(round(0.9 * desktop.screenGeometry().height(), -1))
    if windowHeight > height:
        windowHeight = height

    windowWidth = int(round((width/height) * windowHeight, -1))

    self.window().resize(windowWidth, windowHeight)

    
def printPrepLog(self, s, type=''):
    if type == 'error':
        s = f'''<font color='red'>{s}</font>'''
    elif type == 'bold': 
        s = f'''<b>{s}</b>'''
    self.prepLog_te.append(s)
    # Calculate the maximum vertical scrollbar value
    max_value = self.prepLog_te.verticalScrollBar().maximum()

    # Set the scrollbar value to the maximum to reach the bottom
    self.prepLog_te.verticalScrollBar().setValue(max_value)
    
    QApplication.processEvents()


def findDataColumns(sFileName):
    with open(sFileName, 'r') as sFile:
        saLines = sFile.readlines()
        # Skip all the lines in the start of the file, look for where the 'Well' appears
        for line in saLines:
            saLine = line.split(',')
            if 'Well' in saLine:
                return saLine
    # This is an error
    return None
        

def createPlatemap(self, platesDf, subdirectory_path):
    columns = ['Platt ID', 'Well', 'Compound ID', 'Batch nr', 'Conc mM', 'volume nL']
    platemapDf = pd.DataFrame(columns=columns)
    
    printPrepLog(self, f'Fetching plate data for plates:')
    iNrOfPlates = 0
    for index, row in platesDf.iterrows():
        df = pd.DataFrame()
        plate_value = row['plate']
        plate_data, lSuccess = dbInterface.getPlate(self.token, plate_value)
        if lSuccess:
            iNrOfPlates += 1
            printPrepLog(self, f'{plate_value}')
            df = pd.DataFrame(plate_data, columns=columns)
        else:
            printPrepLog(self, f'Error getting plate {plate_value} {plate_data}', 'error')
        platemapDf = pd.concat([platemapDf if not platemapDf.empty else None, df], ignore_index=True)

    printPrepLog(self, f'Found {iNrOfPlates} plate files')

    excel_filename = 'PLATEMAP.xlsx'
    full_path = os.path.join(subdirectory_path, excel_filename)
    platemapDf.to_excel(full_path, index=False)
    printPrepLog(self, f'Created platemap-file:')
    printPrepLog(self, f'{full_path}', type='bold')

    return full_path


class CancelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Curve fitting calculation')

        self.label = QLabel('Press cancel to stop calculation', self)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel, self)
        self.buttonBox.rejected.connect(self.cancel)

        self.cancelled = False
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def update_label(self, text):
        self.label.setText(text)

    def cancel(self):
        self.cancelled = True
        self.close()
