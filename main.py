#-----------------------------------------------------------------------------------------------------------------------------------------------------
#                                                           PYTHON TEST RUNNER
#-----------------------------------------------------------------------------------------------------------------------------------------------------
#
#    Author: Ethan Lockwood
#
#    Python Version Required: 3.5
#    UI Made using PYQT4
#
#    Description: This is the code for the Python Test Runner Tool, which is the Python version of DV Test Runner. This program runs python unittests
#    via the nose testing framework (which implements the default python unittest framework
#
#-----------------------------------------------------------------------------------------------------------------------------------------------------

import os, sys, traceback, subprocess, time, re, ast, gc, ctypes
import PythonTestRunner_UI, IconCollection, Console_Log, NoFeatureWarning, AdvancedLoadTests, AboutWindow, Override_Window, PySQL_Connector # these are the UI\Local files.
from PyQt4.QtGui import QMainWindow, QFileDialog, QApplication, QTreeWidgetItem, QHeaderView, QDialog, QStatusBar, QTreeWidget, QIcon
from PyQt4.QtCore import Qt, pyqtSignal, QSettings, QObject, QCoreApplication, QTimer
from winreg import OpenKey, CloseKey, CreateKey, KEY_READ, QueryValueEx, HKEY_LOCAL_MACHINE, REG_SZ, KEY_WRITE, SetValueEx
from shutil import copy
from time import strftime
from threading import Thread
from collections import OrderedDict
from os import makedirs
from PyQt4 import QtCore
#from multiprocessing import Process

class PythonTestRunner(QMainWindow, PythonTestRunner_UI.Ui_MainWindow):
    #The line below is the signal point which the Console Log Window is getting result data from.
    newLogData = pyqtSignal(str)
    
    #This function sets up all the button calls and variables (it is called once when the window is made).
    def __init__(self):
        super(PythonTestRunner, self).__init__()
        
        self.settings = QSettings("Elster", "PythonTestRunner")
        if not self.settings.value("geometry") == None:
            self.restoreGeometry(self.settings.value("geometry"))
        if not self.settings.value("windowState") == None:
            self.restoreState(self.settings.value("windowState"))
            
        self.setupUi(self) #this creates the actual window'
        
        SEM_NOGPFAULTERRORBOX = 0x0002 # From MSDN
        ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX)
        
        self.treeWidget.header().setResizeMode(0, QHeaderView.Stretch)
        
        gc.enable()
        ''' TEST CODE FOR A TIMER
        self.testTimer = QTimer()
        self.testTimer.setInterval(1000)
        self.testTimer.connect(QObject, SIGNAL()
        '''
        self.log_window = None
        self.expansionLock = False
        self.testCount = 0 #Tracks the total number of tests loaded.
        self.selTestCount = 0 #tracks the total number of tests selected by the user.
        self.testsDoneCount = 0 #tracks the tests that have been finished in a particular run
        self.testsNotRunCount = 0 #tracks the tests not run.
        self.warningCount = 0 #tracks the number of warnings across all tests
        self.errorCount = 0 #tracks the total error count across all tests
        self.failureCount = 0 #tracks the total failure count across all tests.
        
        self.totalTimeSelected = 0
        
        self.no_feature = None
        self.alt_window = None
        
        self.currentTestDir = "C:\\"
        
        self.sortToggle = True #Toggle value to tell the sort by name function which way to sort.
        
        #self.optionWindow = ConLogOption(self)
        self.icon = IconCollection.Icons()
        
        self.log_window = Console_Log.ConsoleLog(self)
        
        self.networkLogPath = ""
        self.localLogPath = ""
        self.initLogPaths()
        self.logFileBase = ""
        self.networkFilePath = ""
        
        self.initMainFolder()
        
        self.log_window.logPathChange.connect(self.initLogPaths)
        
        self.passed = True
        self.failed = False
        self.error = False
        self.warning = False
        self.testOK = False
        self.testResultList = OrderedDict({})
        self.testsNotRun = []
        self.debug_test_list = []
        self.rerunList = []
        self.cleanResults = OrderedDict({})
        
        self.thread_1 = None
        self.test_process = None
        self.qt_object = QObject()
        
        self.stopTests = False
        
        self.display_time = 0
        
        self.currentTest = None
        
        self.root = self.addNode(self.treeWidget, self.icon.getIcon(5), "Generic", "", False, True)
        
        self.treeWidget.itemChanged.connect(self.handleItemChanged)
        self.treeWidget.itemSelectionChanged.connect(self.showToolTip)
        
        QObject.connect(self.qt_object, QtCore.SIGNAL("done"), self.RerunTests)
        
        self.mainFolderEdit.returnPressed.connect(self.useExistingFolder)
        
        #Database Information Objects
        self.ProductName = None
        self.ProductVersion = None
        self.ProductRevision = None
        self.currentTestSuite = ""
        self.currentTestName = ""
        self.currentTestResult = ""
        self.currentTestStart = ""
        self.currentTestEnd = ""
        self.currentTestLog = ""
        self.currentTestDuration = 0
        
        #Menu Buttons
        #File Menu
        self.actionSave_Selected_Test.triggered.connect(self.saveSelectedTests)
        self.actionSave_Un_selected_Test.triggered.connect(self.noFeature)
        self.actionSave_Selected_Suite_Time.triggered.connect(self.noFeature)
        self.actionLoad_Test_List_To_Select.triggered.connect(self.noFeature)
        self.actionLoad_Test_List_to_Un_select.triggered.connect(self.noFeature)
        self.actionOpen_Test_Session.triggered.connect(self.noFeature)
        self.actionSave_Test_Session.triggered.connect(self.noFeature)
        
        #View Menu
        self.actionConsole_Log.triggered.connect(self.showConsoleLog)
        
        #Options Menu
        self.actionMeter_Builders.triggered.connect(self.noFeature)
        self.actionTest_Station.triggered.connect(self.noFeature)
        self.actionFilter_Suites_By_Author.triggered.connect(self.noFeature)
        
        #Advanced Menu
        self.actionAdvanced_Load_Tests.triggered.connect(self.advancedTestLoader)
        self.actionSave_De_selected_Tests.triggered.connect(self.noFeature)
        self.actionDatabase_Override_Info.triggered.connect(self.databaseOverrideWindow)
        
        #Help Menu
        self.actionHelp_Topics.triggered.connect(self.noFeature)
        self.actionAbout.triggered.connect(self.aboutWindow)
        
        #Window Buttons
        self.runBtn.clicked.connect(self.runBtnSwitch)
        self.folderBtn.clicked.connect(self.getFolder)
        
        #Right Click Context Menu
        #To add further right click menu options: In Qt Designer, View > Action Editor, click Add Action and set the name of the action
        self.treeWidget.addAction(self.actionSort_By_Suite_Name)
        self.treeWidget.addAction(self.actionSort_By_Time_Ascending)
        self.treeWidget.addAction(self.actionSort_By_Time_Descending)
        self.treeWidget.addAction(self.actionClose_All)
        self.treeWidget.addAction(self.actionExpand_All)
        self.treeWidget.addAction(self.actionUnselect_All)
        
        self.actionSort_By_Suite_Name.triggered.connect(self.sortByName)
        self.actionSort_By_Time_Ascending.triggered.connect(self.sortTimeAsc)
        self.actionSort_By_Time_Descending.triggered.connect(self.sortTimeDesc)
        self.actionClose_All.triggered.connect(self.closeAll)
        self.actionExpand_All.triggered.connect(self.expandAll)
        self.actionUnselect_All.triggered.connect(self.uncheckAll)
    
    #this method is an override of the default closeEvent method and includes a means to save the window size/location as well as close the console log window when the main window is closed.
    
    def closeEvent(self, event):
        self.closeConsoleLog()
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        QMainWindow.closeEvent(self, event)
        sys.exit(0)
    
    #setter function to allow the override window to set the necessary values to define the product being tested.
    
    def Set_Database_Values(self, Version, Revision, Product):
        self.ProductVersion = Version
        self.ProductRevision = Revision
        self.ProductName = Product
    
    #window function to open the override options pane
        
    def databaseOverrideWindow(self):
        self.DBOverride = Override_Window.Override_Window(self)
        self.DBOverride.show()
        
    #this function gets the log paths from the registry if they already exist and sets them to C:\ if they do not.
    
    def saveSelectedTests(self):
        testList = []
        
        #fileName = QFileDialog.getOpenFileName(self, caption='Save Selected Tests', directory='C:\\', filter='*.txt')
        fileName = QFileDialog.getSaveFileName(self, caption='Save File Name', directory='C:\\', filter='*.txt')
        
        for suite in range(0, self.root.childCount()):
            testModule = self.root.child(suite)
            for childNum in range(0, testModule.childCount()):
                leaf = testModule.child(childNum)
                if leaf.childCount() == 0:
                    if leaf.checkState(0) == Qt.Checked:
                        testList.append(str(testModule.text(0).replace(".py", "") + "," + leaf.text(0)))
                elif leaf.childCount() > 0:
                    for cLeaf in range(0, leaf.childCount()):
                        classLeaf = leaf.child(cLeaf)
                        if classLeaf.childCount() == 0:
                            if classLeaf.checkState(0) == Qt.Checked:
                                testList.append(str(testModule.text(0).replace(".py", "") + "," + classLeaf.text(0)))
        
        try:
            with open(os.path.normpath(fileName), "w") as f:
                for item in testList:
                    f.write(item + "\n")
            f.close()
        except FileNotFoundError:
            print("File Not Found Error: " + fileName)
        except:
            print("Error: " + sys.exc_info())

    def initLogPaths(self):
        name0 = "LOCAL_LOG_PATH"
        name1 = "NETWORK_LOG_PATH"
        basePathName = os.path.normpath("C:\\")
        local = self.readRegistry(name0)
        if local:
            self.localLogPath = local
            network = self.readRegistry(name1)
            if network:
                self.networkLogPath = network
        else:
            self.writeRegistry(name0, basePathName)
            self.localLogPath = basePathName
            self.writeRegistry(name1, basePathName)
            self.networkLogPath = basePathName
    
    def initMainFolder(self):
        name0 = "TEST_FOLDER_PATH"
        lastUsed = self.readRegistry(name0)
        if lastUsed:
            self.mainFolderEdit.setText(lastUsed)
    
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
        
    def noFeature(self):
        self.no_feature = NoFeatureWarning.NoFeature()
        self.no_feature.show()
        
    def advancedTestLoader(self):
        self.alt_window = AdvancedLoadTests.AdvancedTestLoader(self.root)
        self.alt_window.show()
        
    def consoleLogWindow(self):
        self.log_window.show()
        
    def closeConsoleLog(self):
        self.log_window.close()
    
    #BEGIN RIGHT CLICK MENU FUNCTIONS:
    
    def sortByName(self):
        self.treeWidget.setSortingEnabled(True)
        if self.sortToggle:
            self.treeWidget.sortByColumn(0, Qt.SortOrder(Qt.AscendingOrder))
        else:
            self.treeWidget.sortByColumn(0, Qt.SortOrder(Qt.DescendingOrder))
        self.treeWidget.setSortingEnabled(False)
        self.sortToggle = not self.sortToggle
    
    def sortTimeAsc(self):
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.sortByColumn(1, Qt.SortOrder(Qt.AscendingOrder))
        self.treeWidget.setSortingEnabled(False)
        
    def sortTimeDesc(self):
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.sortByColumn(1, Qt.SortOrder(Qt.DescendingOrder))
        self.treeWidget.setSortingEnabled(False) 
    
    def expandAll(self):
        self.treeWidget.expandAll()
    
    def closeAll(self):
        self.treeWidget.collapseAll()
        
    def uncheckAll(self):
        self.expansionLock = True #this value prevents our checkbox signals from expanding/collapsing the tree
        self.root.setCheckState(0, Qt.Checked)
        self.root.setCheckState(0, Qt.Unchecked)
        self.selTestCount = 0
        self.runNum.setNum(self.selTestCount)
        self.expansionLock = False
    
    #END RIGHT CLICK MENU FUNCTIONS
    
    #The function below controls the operation of the checkboxes and how the nodes expand/collapse as well as the test selected #
    
    def handleItemChanged(self, item, column):
        childCount = item.childCount()
        if item.checkState(column) == Qt.Checked:
            if childCount == 0:
                self.selTestCount += 1
                self.totalTimeSelected += self.getTimeData(item)
                #self.display_time += int(item.data(1, Qt.ToolTipRole))
                #self.updateStatus()
            else:
                for i in range(0, childCount):
                    child = item.child(i)
                    child.setCheckState(0, Qt.Checked)
                    if not self.expansionLock:
                        child.setExpanded(True)
                        item.setExpanded(True)
        elif item.checkState(column) == Qt.Unchecked:
            if childCount == 0:
                self.selTestCount -= 1
                self.totalTimeSelected -= self.getTimeData(item)
                #self.display_time -= int(item.data(1, Qt.ToolTipRole))
                #self.updateStatus()
            else:
                for i in range(0, childCount):
                    child = item.child(i)
                    child.setCheckState(0, Qt.Unchecked)
                    if not self.expansionLock:
                        child.setExpanded(False)
                        item.setExpanded(False)
        self.runNum.setNum(self.selTestCount)
        self.statusbar.showMessage("Time selected: " + str(self.totalTimeSelected), 0)
    
    def getTimeData(self, node):
        if node.data(1, Qt.ToolTipRole) == None: #time related
            return 0
        else:
            return int(node.data(1, Qt.ToolTipRole)) #time related
        
    def updateStatus(self):
        days, minutes = divmod(self.display_time, 60*24)
        hours, minutes = divmod(minutes, 60)
        
        print(self.display_time)
        print(str(days) + " days, " + str(hours) + " hours, " + str(minutes) + " minutes\n")
        
        #a = self.statusBar.showMessage()
        
    
    #this function takes the time for individual tests and puts it in the detail pane.
    
    def showToolTip(self):
        info = ""
        self.detailPane.setText(info)
        node = self.treeWidget.selectedItems()
        if node:
            #timeVal = node[0].data(1, Qt.ToolTipRole)
            #if not ((timeVal == None)):
                #info += "Time = " + str(node[0].data(1, Qt.ToolTipRole)) + "\n\n"
            if not node[0].data(1, Qt.UserRole) == "" and not node[0].data(1, Qt.UserRole) == None:
                info += node[0].data(1, Qt.UserRole)
                self.detailPane.setText(info)
            #self.detailPane.setText(node[0].toolTip(0))
            #self.detailPane.append(node[0].data(1, Qt.ToolTipRole))
    
    #This function gets the folder the user wants the test finder to start at then starts the tree builder.
    
    def getFolder(self):
        testLookupPath = self.mainFolderEdit.text()
        
        if testLookupPath == "":
            testLookupPath = "C:\\"
        
        folderPath = QFileDialog.getExistingDirectory(self, "Select directory", testLookupPath, QFileDialog.ShowDirsOnly)
        
        if not folderPath == "":
            
            self.writeRegistry("TEST_FOLDER_PATH", folderPath)
            self.mainFolderEdit.setText(folderPath)
    
            self.treeWidget.clear()
            self.root = self.addNode(self.treeWidget, self.icon.getIcon(5), "Generic", "", False, True)
    
            self.buildTreeList(folderPath)
            self.testNum.setNum(self.testCount)
    
    def useExistingFolder(self):
        folderPath = self.mainFolderEdit.text()
        self.writeRegistry("TEST_FOLDER_PATH", folderPath)
        
        self.treeWidget.clear()
        self.root = self.addNode(self.treeWidget, self.icon.getIcon(5), "Generic", "", False, True)

        self.buildTreeList(folderPath)
        self.testNum.setNum(self.testCount)
        
        
    # This function builds the actual tree by searching for python files, then parses the file data into a list of files.
        
    def buildTreeList(self, folderPath):
        self.treeWidget.blockSignals(True) #begins signal blocking to ignore time changes during the list build.
        self.testCount = 0
        self.testNum.setNum(self.testCount)
        self.debugList.clear()
        self.debug_test_list.clear()
        self.updateNode(self.root, self.icon.getIcon(5), folderPath)
        for dirpath, dirname, filenames in os.walk(folderPath):
            for filename in [f for f in filenames if f.endswith(".py")]:
                if not filename == "__init__.py":
                    
                    self.getTestData(os.path.normpath(dirpath + "\\" + filename))
                    """
                    self.parseModuleFile((dirpath + "\\" + filename), parentNode)
                    self.getParentInfo(parentNode, os.path.normpath(dirpath + "\\" + filename))
                    if not parentNode == None:
                        self.updateNode(parentNode, None, "", "", self.parentTime(parentNode))
                    """
        self.selTestCount = 0
        self.runNum.setNum(self.selTestCount)
        self.totalTimeSelected = 0
        self.statusbar.showMessage("Time selected: " + str(self.totalTimeSelected), 0)
        self.showDebugList()
        self.treeWidget.blockSignals(False) #ends the signal blocking to allow time changes to occur.
    
    # This function uses the AST module to retrieve the docstring (comments) and function names so they can be loaded into the UI.
    
    def getTestData(self, testPath):
        fd = open(testPath, "r+")
        file_contents = fd.read()
        module = ast.parse(file_contents)
        
        parentNode = self.addNode(self.root, self.icon.getIcon(5), str(os.path.basename(testPath)), "", True)
        
        className = None
        modDescription = ast.get_docstring(module)
        
        parentNode.setData(1, Qt.UserRole, modDescription)
        
        function_definitions = []
        class_function_definitions = []
        
        for node in module.body:
            if isinstance(node, ast.ClassDef):
                className = node.name
                for cNode in node.body:
                    if isinstance(cNode, ast.FunctionDef):
                        class_function_definitions.append(cNode)
                self.functionBreakdown(class_function_definitions, parentNode, className, testPath)
                class_function_definitions = []
                
            elif isinstance(node, ast.FunctionDef):
                function_definitions.append(node)
                
        if len(function_definitions) > 0:
            self.functionBreakdown(function_definitions, parentNode, className, testPath)
    
    def functionBreakdown(self, function_definitions, parentNode, className, testPath):
        testNode = None
        for f in function_definitions:
            if not (isinstance(f, ast.Assert) or isinstance(f, ast.Expr)):
                testName = str(f.name)
                if self.xTest_Ignore(testName): #change this to regex so it ignores xTest_ OLD CODE: "test_".upper() in testName.upper()
                    description = ast.get_docstring(f)
                    if not self.Debug_Check(description):
                        self.testCount += 1
                        self.testNum.setNum(self.testCount)
                        if not className == None:
                            data = testPath + "*:" + className + "." + testName
                            testNode = self.addNode(parentNode, self.icon.getIcon(4), testName, data)
                        else:
                            data = testPath + "*:" + testName
                            testNode = self.addNode(parentNode, self.icon.getIcon(4), testName, data)
                        if not description == None:
                            timeData = self.parseDesc(str(description))
                            if timeData == None:
                                testNode.setData(1, Qt.ToolTipRole, "0") #time related
                            else:
                                testNode.setData(1, Qt.ToolTipRole, str(timeData)) #time related                  
                        testNode.setData(1, Qt.UserRole, description)
                    else:
                        self.debug_test_list.append(className + "." + testName)
        if not parentNode == None:
            self.updateNode(parentNode, None, "", "", self.parentTime(parentNode))
    
    #xTest_Ignore function performs a regular expression to avoid X'd out tests in a python file.
    
    def xTest_Ignore(self, functionName):
        functionName = functionName.lower()
        rg = re.compile('(\Atest_.*)', re.IGNORECASE|re.DOTALL)
        m = rg.search(functionName)
        if not m == None:
            return True
        else:
            return False
    
    def Debug_Check(self, docstring):
        if not docstring == None:
            docstring = docstring.lower()
            rg = re.compile('(debug_test\s*=\s*true)', re.IGNORECASE|re.DOTALL)
            m = rg.search(docstring)
            if not m == None:
                return True
            else:
                return False
        else:
            return False
        
    def showDebugList(self):
        for test in self.debug_test_list:
            self.debugList.append(test)
    #ParseDesc function performs a regular expresseion on the docstring to retrieve the time value.
    #If you want a different Time = differentiation, change test_time in the string below to a new value.
            
    def parseDesc(self, desc):
        rg = re.compile('\s*?(test_time\s*=+\s*)([0-9]+)', re.IGNORECASE|re.DOTALL)
        m = rg.search(desc)
        if not m == None:
            var2 = m.group(2)
            
            return var2
        else:
            return None
    
    # This method calculates the total time for the parent node based on the individual test times.
    
    def parentTime(self, node):
        time = 0
        num = node.childCount()
        if num > 0:
            if node.child(0).childCount() > 0:
                totalTime = 0
                for k in range(0, node.childCount()):
                    time = self.parentTime(node.child(k))
                    #if the class node timing data is desired, it is computed at this point
                    totalTime += time
                return totalTime
            else:
                for i in range(0, num):
                    val = node.child(i).data(1, Qt.ToolTipRole)
                    if not val == None:
                        time += int(val)
                node.setData(1, Qt.ToolTipRole, time) #time related
                return time
        else:
            return 0
    
    # This function adds a node to the tree and sets the various properties of that node.
    
    def addNode(self, parent, icon_, text="", data="", isParent = False, isRoot = False):
        node = QTreeWidgetItem(parent)
        node.setText(0, text)
        node.setCheckState(0, Qt.Unchecked)
        node.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        if isRoot:
            node.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled)
        if isParent:
            node.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
        node.setData(0, Qt.UserRole, data)
        node.setIcon(0, icon_)
        """
        result = self.getTestInfo(data)
        if not result == None:
            if(int(result[0]) >= 0):
                node.setData(1, Qt.ToolTipRole, int(result[0]))
            else:
                node.setData(1, Qt.ToolTipRole, 0)
            node.setToolTip(0, str(result[1]))
        else:
            node.setData(1, Qt.ToolTipRole, 0)
            node.setToolTip(0, "")
        """
        return node
    
    # this method is used to update specific values of a given node such as it's icon, text value, data value, or time value.
    
    def updateNode(self, node, icon_=None, text="", data="", time_=-1):
        if not text == "":
            node.setText(0, text)
        if not data == "":
            node.setData(0, Qt.UserRole, data)
        if not icon_ == None:
            node.setIcon(0, icon_)
        if time_ >= 0:
            node.setData(1, Qt.DisplayRole, time_)
    
    # the following two functions retrieve the data from the header comments of the python files.
    
    def getTestInfo(self, data):
        if data == "":
            return None
        else:
            return self.getTimeDesc(data)#Format: [0, data]
    
    def getTimeDesc(self, data):
        comment = False
        desc = False
        description = ""
        testTime = -1
        results = self.parseTestCall(data)
        try:
            with open(os.path.normpath(results[0]), "r") as f:
                for line in f:
                    if "\'\'\'" in line:
                        comment = not comment
                    if comment:
                        if str(results[1] + ".time = ") in line:
                            n = str(line).replace(str(results[1] + ".time = "), "")
                            testTime = int(n)
                        elif str(results[1] + ".description = {") in line:
                            desc = True
                            if "}" in line:
                                desc = False
                            description += str(line).replace("}", "").replace(str(results[1] + ".description = {"), "") + " "
                            
                        elif desc:
                            if "}" in line:
                                desc = False
                            description += str(line).replace("}", "").replace(str(results[1] + ".description = {"), "") + " "
        except FileNotFoundError:
            print("File Not Found Error in getTimeDesc() using:" + str(results[0]))
        except:
            print("Unknown Error Occurred: " + sys.exc_info())                        
        return [testTime, description.strip()]
    
    # this function breaks down the test call string made when the tree and nodes are created.
    
    def parseTestCall(self, data):
        pieces = data.split("*")
        fullPath = os.path.normpath(pieces[0])
        testName = pieces[1].replace(":", "")
        parts = testName.split(".")
        if len(parts) > 1:
            testName = parts[1]
        return [fullPath, testName]
    
    def refreshUI(self):
        QApplication.processEvents()
    
    def resetTestStats(self):
        self.completeNum.setNum(0)
        self.testsDoneCount = self.failureCount = self.errorCount = self.warningCount = 0
        self.warningNum.setNum(0)
        self.failNum.setNum(0)
        self.errorNum.setNum(0)
        self.notRunNum.setNum(0)
        self.log_window.clearLog()
        self.resetIcons()
        self.testsNotRunCount = 0
        self.testsNotRun = []
    
    #the following method is called by the Run button and calls the entire test runner operation as a separate thread.
    #Once pressed the button changes function to become a "Stop" button, if pressed again, it tries to kill the process.
    
    def runBtnSwitch(self):
        self.treeWidget.blockSignals(True) #prevents time and other values from updating. Stops time re-add during successive runs.
        if self.runBtn.text() == "Run":
            self.thread_1 = Thread(target=self.runTests, args=())           
            myPath = self.localLogPath + "\\Py_Run_" + self.dateStamp() #os.path.normpath("C:\\Python Results\\Py_Run_" + self.dateStamp())
            
            if not os.path.exists(myPath):#if you set a path here, the cwd value of the Popen call will tell MyLog to put the result in that current working directory
                makedirs(myPath)
            if os.path.exists(myPath):
                self.currentTestDir = myPath
            
            self.resetTestStats()

            self.thread_1.start()
            #QApplication.processEvents()

        elif self.runBtn.text() == "Stop":
            self.runBtn.setText("Kill")
            self.stopTests = True
        else:
            self.runBtn.setText("Run")
            self.test_process.kill()
    #This method resets the various values we use during test runs and then steps through the tree to run each test.
    
    def runTests(self):
        self.stopTests = False
        self.runBtn.setText("Stop")
        self.testNum.setNum(self.testCount)
        self.logFileBaseName()
        self.initLogPaths()
        self.testResultList = OrderedDict({})
        
        self.testSessionInfo()
        
        for suite in range(0, self.root.childCount()):
            testModule = self.root.child(suite)
            for childNum in range(0, testModule.childCount()):
                leaf = testModule.child(childNum)
                if leaf.childCount() == 0:
                    if leaf.checkState(0) == Qt.Checked:
                        self.run_(leaf)
                elif leaf.childCount() > 0:
                    for cLeaf in range(0, leaf.childCount()):
                        classLeaf = leaf.child(cLeaf)
                        if not self.stopTests:
                            if classLeaf.childCount() == 0:
                                if classLeaf.checkState(0) == Qt.Checked:
                                    self.run_(classLeaf)
        
        self.finalResults()
        self.createSumFile()
        self.runBtn.setText("Run")
        self.copyLogToNetwork()
        gc.collect()
        self.treeWidget.blockSignals(False) #ends the signal blocking that prevents the time changes from occurring.
        #signal emitted here is to inform the main thread that the test run is complete. The completion signal will trigger the rerun test code from main.
        QObject.emit(self.qt_object, QtCore.SIGNAL("done"))
    
    def run_(self, node):
        testObj = node.data(0, Qt.UserRole)
        self.currentTest = node
        if not self.stopTests:
            self.passed = True
            self.warning = False
            self.failed = False
            self.error = False
            self.testOK = False
            self.consoleLogBreak()
            self.testRunner(testObj)
            self.currentTestDuration = int((time.time() - self.startTime) / 60)
            self.currentTestEnd = self.getSQLFormatDate()
            self.passCheck(testObj)
            self.testsDoneCount += 1
            self.completeNum.setNum(self.testsDoneCount)
            self.pushResultsToDB()
        else:
            self.notRunList(testObj)
    
    def RerunTests(self):
        if (self.runCount.value() > 0) and (not self.stopTests):
            self.runCount.setValue(self.runCount.value() - 1)
            if not len(self.cleanResults) == 0:
                self.totalTimeSelected = 0 #clear time here so that later selections/deselections will re-add time correctly.
                #time.sleep(2)
                #check if the passing or failing tests are what the user wants to rerun.
                if self.rerunCB.checkState() == Qt.Checked:
                    for name, result in self.cleanResults.items():
                        name = name.replace(" -> ", ".")
                        if result == "<FAILED>":
                            self.rerunList.append(name)
                        elif result == "<ERROR>":
                            self.rerunList.append(name)
                    #Since we're still inside the thread we started to run the tests, starting a new thread of the same type crashes python.
                    if not len(self.rerunList) == 0:
                        self.resetTestStats()
                        self.totalTimeSelected = 0
                        self.statusbar.showMessage("Time selected: " + str(self.totalTimeSelected), 0)
                        #load the failed tests back in.
                        self.treeHunt()
                        #run again
                        self.cleanResults.clear()
                        self.rerunList.clear()
                        self.runBtnSwitch()
                        #repeat for the rerun count, unless stop is pressed, use only the list of tests that failed in this run, if none, stop.
                else:
                    for name, result in self.cleanResults.items():
                        name = name.replace(" -> ", ".")
                        self.rerunList.append(name)
                    #load the passing tests back in.
                    if not len(self.rerunList) == 0:
                        self.resetTestStats()
                        self.selTestCount = 0
                        self.runNum.setNum(self.selTestCount)
                        self.statusbar.showMessage("Time selected: " + str(self.totalTimeSelected), 0)
                        #load the passing tests back in
                        self.treeHunt()
                        #run again
                        self.cleanResults.clear()
                        self.rerunList.clear()
                        self.runBtnSwitch()
                        #repeat for all passing tests unless stop is pressed.
        else:
            self.cleanResults.clear()
            self.testResultList.clear()
        
    def treeHunt(self):
        for suite in range(0, self.root.childCount()):
            testModule = self.root.child(suite)
            for childNum in range(0, testModule.childCount()):
                leaf = testModule.child(childNum)
                if leaf.childCount() == 0:
                    leaf.setCheckState(0, Qt.Unchecked)
                    self.testListCheck(testModule, leaf)
                        
                elif leaf.childCount() > 0:
                    for cLeaf in range(0, leaf.childCount()):
                        classLeaf = leaf.child(cLeaf)
                        if classLeaf.childCount() == 0:
                            classLeaf.setCheckState(0, Qt.Unchecked) 
                            self.testListCheck(testModule, classLeaf, leaf)
    
    def testListCheck(self, parent, child, classNode = None):
        if classNode == None:
            testName = parent.data(0, Qt.DisplayRole) + "." + child.data(0, Qt.DisplayRole)
        else:
            testName = parent.data(0, Qt.DisplayRole) + "." + classNode.data(0, Qt.DisplayRole)
        for name in self.rerunList:
            if testName == name:
                if classNode == None:
                    child.setCheckState(0, Qt.Checked)
                else:
                    classNode.setCheckState(0, Qt.Checked)
    
    #this is the actual test run call, it captures stdout and stderr as it is put out by the test, and sends those results to be parsed to the console log window.
        
    def testRunner(self, testCall):
        parts = testCall.split("*")
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        self.currentTestName = self.getTestName(parts[1])
        self.currentTestSuite = os.path.basename(parts[0])
        self.startTime = time.time()
        self.currentTestStart = self.getSQLFormatDate()
        
        self.test_process = subprocess.Popen(["python", os.path.normpath(parts[0]), parts[1]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0, cwd=self.currentTestDir, startupinfo=startupinfo, creationflags=0x8000000)
        
        self.parseResults(self.test_process)
    
    #this method cleans up the raw result data from the test, which arrives in byte code format, then strips any whitespace and logs the cleaned output.
        
    def parseResults(self, results):
        for line in iter(results.stdout.readline, b''): #stdout.readline
            QApplication.processEvents()
            cleanResults = line.decode("utf-8")
            cleanResults = str(cleanResults)
            cleanResults = cleanResults.strip()
            if not cleanResults.isspace():
                #send log to console log window
                self.newLogData.emit(cleanResults)
                #check log data for test result
                self.parseOutput(cleanResults)
                #send log results to log file
                self.logResults((cleanResults + "\n"))
    
    #This function monitors the output stream for the results from the test and sets values and icons accordingly.
    
    def parseOutput(self, testString):
        if self.passed:
            if "failures=" in testString.lower():
                self.failed = True
                self.passed = False
                self.testOK = True
                self.currentTest.setIcon(0, self.icon.getIcon(1))
            elif "errors=" in testString.lower():
                self.error = True
                self.passed = False
                self.failed = True
                self.testOK = True
                self.currentTest.setIcon(0, self.icon.getIcon(0))
            elif "<WARNING>" in testString.upper():
                self.warning = True
                self.currentTest.setIcon(0, self.icon.getIcon(6))
            elif self.testOKCheck(testString):
                self.testOK = True
    
    def testOKCheck(self, lineInput):
        rg = re.compile('.*?(OK)\s*$', re.IGNORECASE|re.DOTALL)
        m = rg.search(lineInput)
        if not m == None:
            return True
        else:
            return False
    
    #this method updates the final test result display points in the GUI main window, such as the icons and the numerical result values.
    
    def passCheck(self, testName):
        result = ""
        
        if not self.testOK:
            self.passed = False
            self.error = True
            self.fail = True
            self.currentTest.setIcon(0, self.icon.getIcon(0))
            
        if self.passed:
            if self.warning:
                self.currentTest.setIcon(0, self.icon.getIcon(3))
                result = "<PASS-WR>"
                self.warningCount += 1
                self.warningNum.setNum(self.warningCount)
            else:
                self.currentTest.setIcon(0, self.icon.getIcon(2))
                result = "<PASSED>"
        else:
            if self.failed:
                result = "<FAILED>"
                self.failureCount += 1
                self.failNum.setNum(self.failureCount)
            if self.error:
                result = "<ERROR>"
                self.errorCount += 1
                self.errorNum.setNum(self.errorCount)
        
        self.testResultList[testName] = result
        self.currentTestResult = (result.strip("<")).strip(">")
        self.update()
        QCoreApplication.processEvents()
    
    def consoleLogBreak(self):
        testBreak = "\n\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n"
        testName = self.currentTest.data(0, Qt.DisplayRole)
        suiteName = self.currentTest.parent().data(0, Qt.DisplayRole)
        testBreak += "Running: " + suiteName + " -> " + testName
        testBreak += "\n\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
        self.newLogData.emit(testBreak)
        self.logResults(testBreak)
    
    #this function captures the names of the tests that were not run
    
    def notRunList(self, testName):
        self.testsNotRunCount += 1
        self.notRunNum.setNum(self.testsNotRunCount)
        self.testsNotRun.append(testName) #[suite] = parts[1]
    
    def resetIcons(self):
        mycount = 0
        for suite in range(0, self.root.childCount()):
            testModule = self.root.child(suite)
            for childNum in range(0, testModule.childCount()):
                leaf = testModule.child(childNum)
                if leaf.childCount() == 0:
                    self.updateNode(leaf, self.icon.getIcon(4))
                    if leaf.checkState(0) == Qt.Checked:
                        mycount += 1
                elif leaf.childCount() > 0:
                    for cLeaf in range(0, leaf.childCount()):
                        classLeaf = leaf.child(cLeaf)
                        if classLeaf.childCount() == 0:
                            self.updateNode(classLeaf, self.icon.getIcon(4))
                            if classLeaf.checkState(0) == Qt.Checked:
                                mycount += 1
        self.selTestCount = mycount
        self.runNum.setNum(self.selTestCount)
    
    #this function creates the information at the top of the log file and console log detailing the conditions of the test.
    
    def testSessionInfo(self):
        
        testList = self.getTestNameList()
        
        testHeader = strftime("%d.%m.%y %H:%M:%S")
        testHeader += "\n--------------- Test Session Information ---------------\n"
        testHeader += "PyTestRunner Session\t[" + strftime("%d/%m/%y %H:%M:%S") + "]\n\n"
        testHeader += "Installed Components:\n\n"
        testHeader += "\tPyTestRunner:\t Version 1.0.0\n\n"
        testHeader += "Selected Tests:\n\n"
        
        for test in iter(testList):
            testHeader += ("\t" + str(test) + "\n")
        
        testHeader += "--------------------------------------------------------\n\n"
        testHeader += "--------------- Running ProjectInfo.exe ---------------\n\n"
        testHeader += "--------------- Begin Test Run ---------------\n\n"
        
        self.newLogData.emit(testHeader)
        self.logResults(testHeader)
    
    #this function walks through the tree and gets a list of all the tests as they appear in their current order.
     
    def getTestNameList(self):
        testList = []
        for suite in range(0, self.root.childCount()):
            testModule = self.root.child(suite)
            for childNum in range(0, testModule.childCount()):
                leaf = testModule.child(childNum)
                if leaf.childCount() == 0:
                    if leaf.checkState(0) == Qt.Checked:
                        testList.append(testModule.text(0) + " -> " + leaf.text(0))
                elif leaf.childCount() > 0:
                    for cLeaf in range(0, leaf.childCount()):
                        classLeaf = leaf.child(cLeaf)
                        if classLeaf.checkState(0) == Qt.Checked:    
                            testList.append(testModule.text(0) + " -> " + classLeaf.text(0))
        return testList
    
    # this function creates the log file and writes the result data to the file.
    
    def logResults(self, resultString):
        #the actual results get pushed to a file here.
        fileName = self.localLogPath + "\\" +  self.logFileBase + ".log"
        fileName = os.path.normpath(fileName)
        try:
            f = open(fileName, 'a+')
            f.write(resultString)
            f.close()
        except FileNotFoundError:
            print("File Not Found Error in logResults() using: " + fileName)
        except:
            print("Unknown Error Occurred in logResults(): " + sys.exc_info())
    #Similar to how TestSessionInfo works, this function gets the end results summary into the logs
    
    def finalResults(self):
        #End results compilation for the console log/log file
        endSession = ""
        endSession += "\n--------------------------------------------------------\n"
        endSession += "PyTestRunner Session Summary\n"
        endSession += "\nTest Results:\n\n"
        for test, result in self.testResultList.items():
            parts = test.split("*")
            testSuite = os.path.basename(parts[0])
            temp = parts[1].split(".")
            if len(temp) > 1:
                testName = temp[1]
            elif len(temp) <= 1:
                testName = temp[0].replace(":", "")
            testName = testSuite + " -> " + testName
            endSession += result + "\t" + testName + "\n"
            self.cleanResults[testName] = result
        for test_ in self.testsNotRun:
            parts = test_.split("*")
            testSuite = os.path.basename(parts[0])
            temp = parts[1].split(".")
            if len(temp) > 1:
                testName = temp[1]
            elif len(temp) <= 1:
                testName = temp[0].replace(":", "")
            testName = testSuite + " -> " + testName
            endSession += "<NOT RUN>" + "\t" + testName + "\n"
        endSession += "\n--------------------------------------------------------\n"
        self.logResults(endSession)
        self.newLogData.emit(endSession)
    
    def pushResultsToDB(self):
        if not self.ProductName == None:
            SQL_Connection = PySQL_Connector.PySQL()
            
            tableName = self.ProductName + "_" + self.ProductVersion + "_" + self.ProductRevision
            
            firmware = (self.ProductVersion + "." + self.ProductRevision)
            
            self.currentTestSuite = self.currentTestSuite.strip(".py")
            
            SQL_Connection.SendResultsToDB(tableName, self.currentTestSuite, self.currentTestName, self.currentTestResult, firmware, self.computerName, self.currentTestStart, self.currentTestEnd, self.currentTestDuration, self.networkFilePath, "1.0")
            #This function performs a copy of the log file created to the network at the end of the test run (it doesn't necessarily have to be to a network location).
    
    def getTestName(self, unprocessed):
        splitData = unprocessed.split(".")
        if len(splitData) > 1:
            return splitData[1]
        else:
            return splitData[0].strip(":")
    
    def copyLogToNetwork(self):
        #copies the result log files to the network
        fileName = self.localLogPath + "\\" + self.logFileBase + ".log"
        fileName = os.path.normpath(fileName)
        sumFileName = self.localLogPath + "\\" + self.logFileBase + ".sum"
        sumFileName = os.path.normpath(sumFileName)
        
        self.networkFilePath = os.path.normpath(self.networkLogPath + "\\" + self.logFileBase + ".log")
        networkSumFilePath = os.path.normpath(self.networkLogPath + "\\" + self.logFileBase + ".sum")
        
        try:
            copy(fileName, self.networkFilePath)
        except FileNotFoundError:
            print("File Not Found Error in copyLogToNetwork with values Local: " + fileName + ", Network: " + self.networkFilePath)
        except:
            print("Unknown Error: " + str(sys.exc_info()))
            
        try:
            copy(sumFileName, networkSumFilePath)
        except FileNotFoundError:
            print("File Not Found Error in copyLogToNetwork with values Local: " + sumFileName + ", Network: " + networkSumFilePath)
        except:
            print("Unknown Error: " + str(sys.exc_info()))
    
    def createSumFile(self):
        sumData = ""
        fileName = self.localLogPath + "\\" +  self.logFileBase + ".sum"
        fileName = os.path.normpath(fileName)
        try:
            f = open(fileName, 'a+')
            for test, result in self.testResultList.items():
                parts = test.split("*")
                testSuite = os.path.basename(parts[0])
                temp = parts[1].split(".")
                if len(temp) > 1:
                    testName = temp[1]
                elif len(temp) <= 1:
                    testName = temp[0].replace(":", "")
                    
                testSuite = testSuite.replace(".py", "")
                if result == "<PASSED>" or result == "<PASS-WR>":
                    baseResult = "PASS"
                    sumData += baseResult + " , " + testSuite + "." + testName + ", " + testName + " Test  -  " + result + "\n"
                elif result == "<FAILED>" or result == "<ERROR>":
                    baseResult = "FAIL"              
                    sumData += baseResult + " , " + testSuite + "." + testName + ", " + testName + " Test  -  " + result + "\n"

            f.write(sumData)
            f.close()
        except FileNotFoundError:
            print("File Not Found Error in createSumFile() using: " + fileName)
        except:
            print("Unknown Error Occurred createSumFile(): " + str(sys.exc_info()))
    
    def showConsoleLog(self):
        self.consoleLogWindow()
    
    #this function computes the basename for the log files and sets it to a global value for consistency later.
    
    def logFileBaseName(self):
        #Builds the base file name to be used on all output files.
        self.logFileBase = ""
        fileName = ""
        fileName += "PyTestRun"
        fileName += self.dateStamp() + "_"
        self.computerName = os.environ['COMPUTERNAME']
        fileName += str(self.computerName).upper()
        self.logFileBase = fileName
    
    def dateStamp(self):
        dstamp = "["
        dstamp += time.strftime("%d-%m-%y")
        dstamp += "]["
        dstamp += time.strftime("%I %M %S %p")
        dstamp += "]"
        return dstamp
    
    def getSQLFormatDate(self):
        return time.strftime("%y-%m-%d")
    
    def aboutWindow(self):
        self.about = AboutWindow.AboutWindow()
        self.about.show()

# this function is what starts the entire execution chain.
        
def main():
    try:
        app = QApplication(sys.argv)
        form = PythonTestRunner()
        form.setWindowTitle('Python Test Runner')
        app_icon = QIcon()
        app_icon.addFile('PTR_ICON.ico')
        app.setWindowIcon(app_icon)
        form.consoleLogWindow()
        form.show()
        app.exec_()
    except KeyboardInterrupt:
        print("Shutdown requested...exiting")
    except Exception:
        traceback.print_exc(file=sys.stdout)
    sys.exit(0)
        
if __name__ == '__main__':
    main()
