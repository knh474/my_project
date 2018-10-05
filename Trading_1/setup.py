
from cx_Freeze import setup, Executable
import sys
import os

os.environ['TCL_LIBRARY'] = "C:\\Program Files\\Python35\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\Program Files\\Python35\\tcl\\tk8.6"

buildOptions = dict(packages = ['sys','pandas','PyQt5','time','telegram','requests','PyQt5.uic.port_v2.invoke'])

base = None
if sys.platform == "win32":
    base = "Win32GUI"

exe = [Executable("Trader_v4.py", base = base)]

setup(
    name = 'Trader_v4',
    version = '0.4',
    author = 'knh474',
    description = 'trading',
    options = dict(build_exe = buildOptions),
    executables = exe
)
