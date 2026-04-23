import maya.cmds as mc
from PySide6.QtWidgets import QWidget, QMainWindow
from PySide6.QtCore import Qt
import maya.OpenMayaUI as omui
from shiboken6 import wrapInstance


def GetMayaMainWindow()->QMainWindow:
    mayaMainWindow = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mayaMainWindow), QMainWindow)

def RemoveWidgetWithName(objectName):
    for widget in GetMayaMainWindow().findChildren(QWidget, objectName):
        widget.deleteLater()

class MayaWidget(QWidget):
    def __init__(self):
        super().__init__(parent=GetMayaMainWindow())
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle("Maya Widget")
        RemoveWidgetWithName(self.GetWidgetHash())
        self.setObjectName(self.GetWidgetHash())

    def GetWidgetHash(self):
        return "1bc0cc54f3a85de63deb1fff2e842c31e4f0a6b4fe0c57f9e8d80466471a4d47"
