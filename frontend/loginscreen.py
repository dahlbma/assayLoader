import sys, logging
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMessageBox

from assaylib import *
from singlePointScreen import SinglePointScreen
from doseResponseScreen import DoseResponseScreen


class LoginScreen(QMainWindow):
    def __init__(self, appName):
        super(LoginScreen, self).__init__()
        self.mod_name = "login"
        self.appName = appName
        logger = logging.getLogger(self.mod_name)
        loadUi(resource_path("assets/welcomescreen.ui"), self)
        self.login.clicked.connect(self.loginfunction)
        saDatabases = None
        try:
            saDatabases = dbInterface.getDatabase()
        except Exception as e:
            send_msg("Connection Error",
                     f"AssayLoader has encountered a fatal error:\n\n{str(e)}\n\nPlease restart AssayLoader.",
                     icon=QMessageBox.Critical, e=e)
            sys.exit()
        self.server_cb.addItems(saDatabases)
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self.loginfunction()
    
    def loginfunction(self):
        
        user = self.usernamefield.text()
        password = self.passwordfield.text()
        database = self.server_cb.currentText()
        if len(user) == 0 or len(password) == 0:
            self.errorlabel.setText("Please input all fields")
        else:
            self.errorlabel.setText("")
        
        try:
            r = dbInterface.login(user, password, database)
        except Exception as e:
            self.errorlabel.setText("Bad Connection")
            send_msg("Error Message", str(e), QMessageBox.Warning, e)
            logging.getLogger(self.mod_name).error(str(e))
            return
        if r.status_code != 200:
            self.errorlabel.setText("Wrong username/password")
            return
        self.jwt_token = r.content
        self.startApp(database)

    def startApp(self, db):
        test = 'false'
        if db != 'Live':
            test = 'true'

        app = QtCore.QCoreApplication.instance()
        self.window().setWindowTitle(f"{self.appName} {db}")

        #init
        singlePoint = SinglePointScreen(self.jwt_token, test)
        doseResponse = DoseResponseScreen(self.jwt_token, test)
        
        #add screens to stackedwidget
        self.window().addWidget(singlePoint)
        self.window().addWidget(doseResponse)
        gotoSP(self)
