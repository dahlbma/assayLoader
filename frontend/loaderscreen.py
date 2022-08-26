import re, sys, os, logging
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt

from assaylib import *

class LoaderScreen(QMainWindow):
    def __init__(self, token, test):
        super(LoaderScreen, self).__init__()
        self.token = token
        self.mod_name = "loader"
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/loaderwindow.ui"), self)
        
        try:
            js = dbInterface.getSinglePointConfig(self.token)
            res1 = json.loads(js)
            h1 = [str(h) for h in res1]
            js = dbInterface.getDoseResponseConfig(self.token)
            res2 = json.loads(js)
            h2 = [str(h) for h in res2]
        except:
            print("oops")   

        self.sp_table.setColumnCount(len(h1))
        self.sp_table.setHorizontalHeaderLabels(h1)
        self.dr_table.setColumnCount(len(h2))
        self.dr_table.setHorizontalHeaderLabels(h2)


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            if self.loader_tab_wg.currentIndex() == 1:
                return
            else: # tab 0, no btn
                return

    def tabChanged(self):
        page_index = self.loader_tab_wg.currentIndex()
        if page_index == 0:
            return
        elif page_index == 1:
            return

