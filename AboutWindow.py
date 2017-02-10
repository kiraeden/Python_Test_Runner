'''
Created on Jul 8, 2016

@author: LockwoodE
'''

from PyQt4.QtGui import QWidget
import PTR_About_Window

class AboutWindow(QWidget, PTR_About_Window.Ui_AboutWindow):
    def __init__(self):
        super(AboutWindow, self).__init__()
        
        self.setupUi(self)
        
        self.closeWindow.clicked.connect(self.closeAboutWindow)
        
        self.label_2.setText("Version 1.4") #set version number here on new build!
        
    def closeAboutWindow(self):
        self.close()