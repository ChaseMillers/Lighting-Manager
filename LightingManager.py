from Qt import QtWidgets, QtCore, QtGui
import pymel.core as pm
# partial lets you create a object will tekk you witch function
#  to call later and what arguments to give it
from functools import partial

class LightManager(QtWidgets.QDialog):

    lightTypes = {
        "Point Light": pm.pointLight,
        "Spot Light": pm.spotLight,
        "Directional Light": pm.directionalLight,
        # partial lets you store the aruments with the function to call later
        # this is done because you cant just give the function name for Area Light
        "Area Light": partial(pm.shadingNode, 'areaLight', asLight=True),
        "Volume Light": partial(pm.shadingNode, 'volumeLight', asLight=True)
    }

    def __init__(self):
        super(LightManager, self).__init__()
        self.setWindowTitle('Lighting Manager')
        self.buildUI()

    def buildUI(self):
        layout = QtWidgets.QGridLayout(self)

        self.lightTypeCB = QtWidgets.QComboBox()
        # .sorted list the library in alphabetical order
        for lightType in sorted(self.lightTypes):
            self.lightTypeCB.addItem(lightType)
        # the two digits equal row and column for the widget
        layout.addWidget(self.lightTypeCB, 0, 0)

        createBtn = QtWidgets.QPushButton('Create')
        createBtn.clicked.connect(self.createLight)
        layout.addWidget(createBtn, 0, 1)

    def createLight(self):
        lightType = self.lightTypeCB.currentText()
        func = self.lightTypes[lightType]

        light = func()


def showUI():
    ui = LightManager()
    ui.show()
    return ui
