'''
Created on Dec 16, 2015

@author: LockwoodE
'''

from PyQt4.QtGui import QFileDialog, QDialog
from PyQt4.QtCore import pyqtSignal
from winreg import OpenKey, CloseKey, CreateKey, KEY_READ, QueryValueEx, HKEY_LOCAL_MACHINE, REG_SZ, KEY_WRITE, SetValueEx
import ConsoleLogOption_UI
import os

class ConLogOption(QDialog, ConsoleLogOption_UI.Ui_ConLogOptWindow):
    
    newLogPath = pyqtSignal(bool)
    def __init__(self):
        super(ConLogOption, self).__init__()
        self.setupUi(self)
        
        self.localLog = ""
        self.networkLog = ""
        
        self.initFields()
        
        self.logPath.setText(self.readRegistry("LOCAL_LOG_PATH"))
        self.networkPath.setText(self.readRegistry("NETWORK_LOG_PATH"))
        
        self.okBtn.clicked.connect(self.acceptInput)
        self.cancelBtn.clicked.connect(self.closeWindow)
        self.filePushBtn.clicked.connect(self.fileNetPush)
        self.logFileBtn.clicked.connect(self.selLogPath)
        self.netwPathBtn.clicked.connect(self.selNetworkPath)
        
        #self.fontCB.clicked.connect()
    
    def closeEvent(self, event):
        self.localLog = self.readRegistry("LOCAL_LOG_PATH")
        self.networkLog = self.readRegistry("NETWORK_LOG_PATH")
        self.logPath.setText(self.localLog)
        self.networkPath.setText(self.networkLog)
    
    def initFields(self):
        name0 = "LOCAL_LOG_PATH"
        name1 = "NETWORK_LOG_PATH"
        basePathName = os.path.normpath("C:\\")
        local = self.readRegistry(name0)
        if local:
            self.localLog = local
            network = self.readRegistry(name1)
            if network:
                self.networkLog = network
        else:
            self.writeRegistry(name0, basePathName)
            self.localLog = basePathName
            self.writeRegistry(name1, basePathName)
            self.networkLog = basePathName
    
    def readRegistry(self, value):
        REG_PATH = 'SOFTWARE\ABB\PythonTestRunner'
        try:
            root_key = OpenKey(HKEY_LOCAL_MACHINE, REG_PATH, 0, KEY_READ)
            [Pathname,regtype]=(QueryValueEx(root_key, value))
            CloseKey(root_key)
            if "" == Pathname:
                raise WindowsError
            else:
                return Pathname
        except WindowsError:
            return False
    
    def writeRegistry(self, myKey, value):
        REG_PATH = 'SOFTWARE\ABB\PythonTestRunner'
        try:
            keyval=r'SOFTWARE\ABB\PythonTestRunner'
            if not os.path.exists("keyval"):
                key = CreateKey(HKEY_LOCAL_MACHINE,keyval)
            Registrykey= OpenKey(HKEY_LOCAL_MACHINE, REG_PATH, 0, KEY_WRITE)
            SetValueEx(Registrykey, myKey, 0, REG_SZ, value)
            CloseKey(Registrykey)
            return True
        except WindowsError:
            return False
    
    def fileNetPush(self):
        pass
        #empty function placeholder for the Push Log File to Network operation.
    
    def closeWindow(self):
        self.localLog = self.readRegistry("LOCAL_LOG_PATH")
        self.networkLog = self.readRegistry("NETWORK_LOG_PATH")
        self.close()
    
    def acceptInput(self):
        # I could emit all the changes here when the OK button is pressed.
        
        if self.logPath.text() != self.localLog:
            self.localLog = self.logPath.text()
        
        if self.networkPath.text() != self.networkLog:
            self.networkLog = self.networkPath.text()
        
        self.writeRegistry("LOCAL_LOG_PATH", self.localLog)
        self.writeRegistry("NETWORK_LOG_PATH", self.networkLog)
        self.newLogPath.emit(True)
        self.close()
        
    def selLogPath(self):
        filePath = QFileDialog.getExistingDirectory(self, "Select directory", self.localLog, QFileDialog.ShowDirsOnly)
        if not filePath == self.localLog:
            self.logPath.setText(filePath)
            self.localLog = filePath
    
    def selNetworkPath(self):
        
        filePath = QFileDialog.getExistingDirectory(self, "Select directory", self.networkLog, QFileDialog.ShowDirsOnly)
        if not filePath == self.networkLog:
            self.networkPath.setText(filePath)
            self.networkLog = filePath