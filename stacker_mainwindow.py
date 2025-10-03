# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtCore import QObject, QThread, Signal
#from PySide6.QtGui import QAction

#from PyQt6.QtWidgets import (
#    QMainWindow, QApplication,
#    QLabel, QToolBar, QStatusBar
#)
#from PyQt6.QtGui import QAction, QIcon
#from PyQt6.QtCore import Qt

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from stacker_ui_form import Ui_MainWindow
from stacker2 import stacker

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.comboBox.setCurrentIndex(1)
        self.ui.progressBar.setValue(0)
        self.ui.lineEdit.setText("/home/ian/snowdrops/2025_02_20/png/set4a/aligned")
        self.ui.lineEdit_2.setText("/home/ian/snowdrops/2025_02_20/png/set4a/output/output.png")
        self.make_connections()

    def make_connections(self):
        self.ui.actionSelect_input_path.triggered.connect(self.select_input)
        self.ui.actionSelect_output_file.triggered.connect(self.select_output)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionRestore_default_settings.triggered.connect(self.set_defaults)
        self.ui.actionAbout.triggered.connect(self.about)
        self.ui.actionQuickstart.triggered.connect(self.quickstart)
        self.ui.pushButton_2.clicked.connect(self.stack)

    def select_input(self):
        folderpath=QFileDialog.getExistingDirectory(self, 'Select Input Folder')
        self.ui.lineEdit.setText(folderpath)
        outputpath=folderpath+'/output.png'
        self.ui.lineEdit_2.setText(outputpath)


    def select_output(self):
        filepath=QFileDialog.getSaveFileName(self, 'Select Output File')
        self.ui.lineEdit_2.setText(filepath[0])

    def set_defaults(self):
        self.ui.comboBox.setCurrentIndex(1)
        self.ui.comboBox_2.setCurrentIndex(0)
        self.ui.comboBox_3.setCurrentIndex(0)
        self.ui.checkBox.setChecked(False)

    def about(self):
        QMessageBox.about(
            self, "Focus Stack",
            "Focus stacking software using the Laplacian<br>"
            "pyramid method. Written in Python using the QT<br>"
            "and OpenCV libraries.<br>",
        )

    def quickstart(self):
        QMessageBox.about(
            self, "Focus Stack",
            "The program will attempt to stack all the images in the\
            selected input folder. All the files in this folder\
            must be the same size and in common image formats\
            (eg .jpg, png) with 8 or 16 bit colour depth. Raw formats are\
            not supported. Choose the input folder first, then alter\
            the output file name if needed<br>\
            Stack quality may be improved by changing the default filter\
            size. If the check box is set, the Laplacian pyramid of the\
            final merged image will be saved. This will be a large file.",
        )

    def reportProgress(self, message):
        self.ui.progressBar.setValue(int(message))

    def reportFinished(self):
        self.ui.progressBar.setValue(100)

    def reportZero(self):
        self.ui.progressBar.setValue(0)

    def sayComplete(self):
        self.ui.textEdit.append("Stacking complete")

    def sayAbandoned(self):
        self.ui.textEdit.append("Stacking abandoned")

    def show_message(self, message):
        self.ui.textEdit.append(message)


    def stack(self):
        choice=[False, True]
        ipp=str(self.ui.lineEdit.text()) # Input path
        opf=str(self.ui.lineEdit_2.text()) # Output file
        efs=self.ui.comboBox.currentIndex() # Energy filter size
        efs=2*efs+3
        smm=self.ui.comboBox_2.currentIndex() # Stack merge method
        smm=choice[smm] # True for merge by colour, False for gray
        inm=self.ui.comboBox_3.currentIndex() # Image normalisation method
        inm=choice[inm] # True for scaling, false for clip       
        spy=self.ui.checkBox.isChecked() # Save pyramid flag
        params=[ipp, opf, efs, spy, smm, inm]
        self.thread=QThread()
        self.worker=stacker(params)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.reportProgress)
        self.worker.message.connect(self.show_message)
        self.worker.finished.connect(self.sayComplete)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.reportFinished)
        self.thread.finished.connect(lambda: self.ui.pushButton.setEnabled(True))
        self.thread.finished.connect(lambda: self.ui.pushButton_2.setEnabled(True))

        self.worker.abandoned.connect(self.sayAbandoned)
        self.worker.abandoned.connect(self.reportZero)
        self.worker.abandoned.connect(self.thread.quit)
        self.worker.abandoned.connect(self.worker.deleteLater)
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)

        self.thread.start()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
