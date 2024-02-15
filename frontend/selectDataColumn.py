from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout, QComboBox

class SelectDataColumn(QDialog):
    def __init__(self, columns):
        super().__init__()

        self.setWindowTitle("Select a datacolumn")
        self.columns = columns
        self.selectedColumn = ''
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Create a combo box
        self.comboBox = QComboBox()
        self.comboBox.addItems(self.columns)
        layout.addWidget(self.comboBox)

        # Create a button to confirm selection
        selectButton = QPushButton("Select Harmony data column")
        selectButton.clicked.connect(self.onSelect)
        layout.addWidget(selectButton)

        self.setLayout(layout)

    def onSelect(self):
        # Get the selected item
        selected_item = self.comboBox.currentText()
        self.selectedColumn = selected_item
        self.accept()

