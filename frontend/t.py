import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QCheckBox, QFrame


class DynamicCheckboxApp(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        self.create_checkbox_btn = QPushButton('Create Checkbox', self)
        self.create_checkbox_btn.clicked.connect(self.create_checkbox)
        self.create_checkbox_btn.setFixedSize(120, 30)  # Set fixed size

        self.delete_checkbox_btn = QPushButton('Delete Checkbox', self)
        self.delete_checkbox_btn.clicked.connect(self.delete_checkbox)
        self.delete_checkbox_btn.setFixedSize(120, 30)  # Set fixed size

        self.container_frame = QFrame(self)
        self.container_frame.setFrameShape(QFrame.Box)  # Add a frame around the container
        self.container_frame.setFixedSize(400, 60)  # Set fixed size for the container

        self.checkbox_layout = QHBoxLayout(self.container_frame)

        self.layout.addWidget(self.create_checkbox_btn)
        self.layout.addWidget(self.delete_checkbox_btn)
        self.layout.addWidget(self.container_frame)

        # Add 15 invisible checkboxes to the container
        self.checkboxes = [QCheckBox(f'Checkbox {i + 1}', self) for i in range(15)]
        for checkbox in self.checkboxes:
            checkbox.setVisible(False)
            self.checkbox_layout.addWidget(checkbox)

        self.setLayout(self.layout)

        self.setGeometry(300, 300, 500, 200)
        self.setWindowTitle('Dynamic Checkbox App')
        self.show()

    def create_checkbox(self):
        for checkbox in self.checkboxes:
            if not checkbox.isVisible():
                checkbox.setVisible(True)
                return

    def delete_checkbox(self):
        for checkbox in reversed(self.checkboxes):
            if checkbox.isVisible():
                checkbox.setVisible(False)
                return


def main():
    app = QApplication(sys.argv)
    ex = DynamicCheckboxApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
