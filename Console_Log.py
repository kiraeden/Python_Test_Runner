'''
Created on Dec 16, 2015

@author: LockwoodE
'''

from PyQt4.QtGui import QWidget, QFileDialog
from PyQt4.QtCore import QFile, QIODevice, QSettings, pyqtSignal
import ConsoleLog_UI
import Option_Window, Log_Search

class ConsoleLog(QWidget, ConsoleLog_UI.Ui_ConsoleLog):
    logPathChange = pyqtSignal(bool)
    def __init__(self, parent):
        super(ConsoleLog, self).__init__()
        self.settings = QSettings("Elster", "ConsoleLog")
        if not self.settings.value("geometry") == None:
            self.restoreGeometry(self.settings.value("geometry"))
        self.setupUi(self)
        
        self.optionWindow = Option_Window.ConLogOption()
        
        self.searchWindow = Log_Search.LogSearchWindow(self)
                
        self.searchLogBtn.clicked.connect(self.searchLog)
        self.clearLogBtn.clicked.connect(self.clearLog)
        self.printLogBtn.clicked.connect(self.printLog)
        self.optionBtn.clicked.connect(self.optionDialog)
        self.saveLogBtn.clicked.connect(self.saveLog)
        
        parent.newLogData.connect(self.handleTest)
        
        self.optionWindow.newLogPath.connect(self.newLog)
        
    def closeEvent(self, event):
        self.optionWindow.close()
        self.searchWindow.close()
        self.settings.setValue("geometry", self.saveGeometry())
        QWidget.closeEvent(self, event)
    
    def handleTest(self, testCall):
        #self.consoleLogTxt.append("Sample console Log test text...")
        self.consoleLogTxt.append(testCall)
    
    def newLog(self, value):
        self.logPathChange.emit(True)
    
    def searchLog(self):
        self.searchWindow.show()
    
    def clearLog(self):
        self.consoleLogTxt.clear()
        
    def printLog(self):
        #need to find a way to print the log, this also needs a confirmation checkbox
        self.consoleLogTxt.append("Temp test data\n")
    
    def optionDialog(self):
        #need a window that lets the user set the output points for the log files.
        self.optionWindow.show()
    
    def searchDialog(self):
        self.searchWindow.show()
        
    def saveLog(self):
        #need to make a way to save the log file.
        QFD = QFileDialog(self)
        f = QFD.getSaveFileName(self, "Save the Current Log...", "C:\\", "*.log")
        if not "." in f:
            f += ".log"
        file = QFile(f)
        file.open(QIODevice.ReadWrite)
        file.write(self.consoleLogTxt.toPlainText())
        file.close()