from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QDialog, QComboBox, QHBoxLayout


class ItemSelectionDialog(QDialog):
    def __init__(self, parent, items):
        super().__init__()

        self.setWindowTitle("Select an Item")
        self.items = items
        self.parent = parent
        
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Create a combo box
        self.comboBox = QComboBox()
        self.comboBox.addItems(self.items)
        layout.addWidget(self.comboBox)

        # Create a button to confirm selection
        selectButton = QPushButton("Select")
        selectButton.clicked.connect(self.onSelect)
        layout.addWidget(selectButton)

        self.setLayout(layout)

    def onSelect(self):
        # Get the selected item
        selected_item = self.comboBox.currentText()
        self.parent.selectedItemLabel.setText(selected_item)
        self.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Item Selection Example")
        self.setGeometry(100, 100, 400, 200)

        # Create a push button
        self.pushButton = QPushButton("Select Item", self)
        self.pushButton.setGeometry(50, 50, 100, 30)
        self.pushButton.clicked.connect(self.showItemSelectionDialog)

        # Create a label to display selected item
        self.selectedItemLabel = QLabel("", self)
        self.selectedItemLabel.setGeometry(200, 50, 150, 30)

    def showItemSelectionDialog(self):
        # Create an instance of ItemSelectionDialog
        dialog = ItemSelectionDialog(self, ["Item 1", "Item 2", "Item 3"])
        
        # If dialog is accepted, update the label with the selected item
        if dialog.exec_() == QDialog.Accepted:
            selected_item = dialog.result()
            self.selectedItemLabel.setText(selected_item)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
