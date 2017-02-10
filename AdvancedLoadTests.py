'''
Created on Dec 30, 2015

@author: LockwoodE
'''
import ALTWindow, os, sys
from PyQt4.QtGui import QWidget, QFileDialog
from PyQt4.Qt import Qt

class AdvancedTestLoader(QWidget, ALTWindow.Ui_Form):
    
    def __init__(self, treeWidget=None):
        super(AdvancedTestLoader, self).__init__()
        self.setupUi(self)
        
        self.cancelBtn.clicked.connect(self.closeWindow)
        self.findFileBtn.clicked.connect(self.getFile)
        self.loadBtn.clicked.connect(self.loadTestList)
        
        self.myTree = treeWidget
        
        self.importList = []
        self.importFileName = ""
        
        self.timeLimit = 0
        self.timeCheck = False
        self.timeSum = 0
        self.removeTests = False
        self.hasCompName = False
        
    def loadTestList(self):
        
        if(self.timeLimitCB.checkState() == Qt.Checked):
            self.timeLimit = int(self.timeEdit.text())
            self.timeCheck = True
        if(self.removeTestsCB.checkState() == Qt.Checked):
            self.removeTests = True
        if(self.hasCompCB.checkState() == Qt.Checked):
            self.hasCompName = True
        
        computerName = os.environ['COMPUTERNAME']
        if self.hasCompName:
            if computerName in self.fileEntry:
                self.treeHunt(self.myTree)
        else:     
            self.treeHunt(self.myTree)
        
        if self.removeTests:
            with open(os.path.normpath(self.fileEntry.text()), "w") as f:
                for item in self.importList:
                    f.write(item + "\n")
            f.close()
        self.close()
        
    #given the number of operations this could lead to, scanning the file more than once could become n^2 vs log(n) for this function. So the best option may be to read in the entire list,
    #delete the file, then recreate the file via the list of items I read in from the file, minus the items taken out if the user requests test removal from the list.
    
        
    def treeHunt(self, node):
        #steps through the test tree list down to each lead node then performs testListCheck
        self.testListImport()
        for suite in range(0, node.childCount()):
            testModule = node.child(suite)
            for childNum in range(0, testModule.childCount()):
                leaf = testModule.child(childNum)
                if leaf.childCount() == 0:
                    self.testListCheck(testModule, leaf)
                        
                elif leaf.childCount() > 0:
                    for cLeaf in range(0, leaf.childCount()):
                        classLeaf = leaf.child(cLeaf)
                        if classLeaf.childCount() == 0:    
                            self.testListCheck(testModule, classLeaf, leaf)
    
    def testListCheck(self, parent, child, classNode = None):
        #checks a given node's testClass,testName against each line of the imported text list of test names.
        #test list's passed must be of the form CLASSNAME,TESTNAME
        testName = parent.text(0).replace(".py","") + "," + child.text(0) #this has been modified to make it's lookup string match the excel sheet test list output.
        for name in self.importList:
            if testName in name:
                if self.timeCheck:
                    if (self.timeSum + int(child.data(1, Qt.ToolTipRole))) <= self.timeLimit:  
                        self.importList.remove(name)
                        child.setCheckState(0, Qt.Checked)
                        child.setExpanded(True)
                        parent.setExpanded(True)
                        #parent.setCheckState(0, Qt.Checked)
                        self.myTree.setExpanded(True)
                        if not classNode == None:
                            classNode.setExpanded(True)
                        self.timeSum += int(child.data(1, Qt.ToolTipRole))
                else:
                    self.importList.remove(name)
                    child.setCheckState(0, Qt.Checked)
                    child.setExpanded(True)
                    parent.setExpanded(True)
                    #parent.setCheckState(0, Qt.Checked)
                    self.myTree.setExpanded(True)
                    if not classNode == None:
                        classNode.setExpanded(True)
    
    def testListImport(self):
        try:
            with open(os.path.normpath(self.fileEntry.text()), 'r+') as f:
                for line in f:
                    self.importList.append(str(line).strip())
                f.close()
                
            if self.removeTests:
                os.remove(os.path.normpath(self.fileEntry.text()))
                
        except FileNotFoundError:
            print("File Not Found Error Occurred in Advanced Load Tests...")
        except:
            print("Unknown Error Occurred: " + sys.exc_info())
            
    def getFile(self):
        self.importFileName = QFileDialog.getOpenFileName(self, caption='Select a List of Tests...', directory='C:\\', filter='*.txt')
        self.fileEntry.setText(self.importFileName)
    
    def closeWindow(self):
        self.close()