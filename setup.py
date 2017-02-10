'''
Created on Sep 10, 2015

@author: Ethan Lockwood
'''
from cx_Freeze import setup, Executable

includes = ["sip","atexit"]

exe = Executable(
    script = "main.py",
    base = "Win32GUI",
    targetName = "Python Test Runner.exe",
    icon="PTR_ICON.ico"
)
 
setup(
    name = "Python Test Runner",
    version = "1.1.0",
    description = "Runs Python tests and logs the results.",
    options = {"build_exe": {"includes": includes}},
    executables = [exe]
)