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
        self.addLight(light)

    def addLight(self, light):
        widget = LightWidget(light)
        self.scrollLayout.addWidget(widget)
        widget.onSolo.connect(self.onSolo)

    def onSolo(self, value):
        lightWidgets = self.findChildren(LightWidget)
        for widget in lightWidgets:
            if widget != self.sender():
                widget.disableLight(value)

class LightWidget(QtWidgets.QWidget):

    onSolo = QtCore.Signal(bool)

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

        soloBtn = QtWidgets.QPushButton('Solo')
        soloBtn.setCheckable(True)
        soloBtn.toggled.connect(lambda val: self.onSolo.emit(val))
        layout.addWidget(soloBtn, 0, 1)

        deleteBtn = QtWidgets.QPushButton('X')
        deleteBtn.clicked.connect(self.deleteLight)
        deleteBtn.setMaximumWidth(10)
        layout.addWidget(deleteBtn, 0, 2)

        intensity = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        intensity.setMinimum(1)
        intensity.setMinimum(1000)
        intensity.setValue(self.light.intensity.fet())
        intensity.valueChanged.connect(lambda val: self.light.intensity.set(val))
        layout.addWidget(intensity, 1, 0, 1, 2)

    def disableLight(self, value):
        self.name.setChecked(not value)

    def deleteLight(self):
        # somtimes these can conflict so best to run all 3 together. 
        # remove from light manager
        self.setParent(None)
        # set visiblity to false
        self.setVisible(False)
        # delete later when possible. 
        self.deleteLater()

        pm.delete(self.light.getTransform())

def showUI():
    ui = LightManager()
    ui.show()
    return ui
