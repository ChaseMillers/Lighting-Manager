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

        scrollWidget = QtWidgets.QWidget()
        scrollWidget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.scrollLayout = QtWidgets.QVBoxLayout(scrollWidget)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(scrollWidget)
        # add to row 1, at colmn 0, take 1 row, and 2 columns
        layout.addWidget(scrollArea, 1, 0, 1, 2)

    def createLight(self):
        lightType = self.lightTypeCB.currentText()
        func = self.lightTypes[lightType]

        light = func()
        widget = LightWidget(light)
        self.scrollLayout.addWidget(widget)

class LightWidget(QtWidgets.QWidget):

    def __init__(self, light):
        super(LightWidget, self).__init__()
        if isinstance(light, basestring):
            light = pm.PyNode(light)

        self.light = light
        self.buildUI()
    
    def buildUI(self):
        layout = QtWidgets.QGridLayout(self)

        self.name = QtWidgets.QCheckBox(str(self.light.getTransform()))
        self.name.setChecked(self.light.visibility.get())
        # lambda accepts a value then uses it as a variable, basicly its a function 
        # you only use once because it dosen't have or need a name. "anomas function"
        self.name.toggled.connect(lambda val: self.light.getTransform().visibility.set(val))
        layout.addWidget(self.name, 0, 0)

def showUI():
    ui = LightManager()
    ui.show()
    return ui
