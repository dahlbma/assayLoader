import sys, requests, json, os, subprocess, platform, datetime, logging, dbInterface, re
from unittest import result
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidget, QTableWidgetItem, QWidget
from PyQt5.QtWidgets import QProgressBar, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
from PyQt5 import sip

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


def resetPrepLog(self):
    self.prepLog_te.setText('')

    
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
        
