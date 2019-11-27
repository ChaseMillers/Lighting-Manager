import os
from Qt import QtWidgets, QtCore, QtGui
import pymel.core as pm
# partial lets you create a object will tekk you witch function
#  to call later and what arguments to give it
from functools import partial
import Qt
import logging 
from maya import OpenMayaUI as omui
import json
import time

logging.basicConfig()
logger = logging.getLogger('LightingManager')
# switch to INFO to DEBUG when testing
logger.setLevel(logging.INFO)

if Qt.__binding__== 'pySide':
    logger.debug('Using Pyside with shiboken')
    from shiboken import wrapInstance
    from Qt.QtCore import Signal
elif Qt.__binding__.startswith('PyQt'):
    logger.debug('Using PyQt with sip')
    from sip import wrapinstance as wrapInstance
    from Qt.QtCore import pyqtSignal as Signal
else: 
    logger.debug('Using Pyside2 with shiboken')
    from shiboken2 import wrapInstance
    from Qt.QtCore import Signal

def getMayaMainWindow():
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr

#for docking to side of maya
def getDock(name='LightingManagerDock'):
    deleteDock(name)
    ctrl = pm.workspaceControl(name, dockToMainWindow=('right', 1), label="Lighting Manager")
    qtCtrl = omui.MQtUtil_findControl(ctrl)
    ptr = wrapInstance(long(qtCtrl), QtWidgets.QWidget)
    return ptr 

def deleteDock(name='LightingManagerDock'):
    if pm.workspaceControl(name, query=True, exists=True):
        pm.deleteUI(name)

class LightManager(QtWidgets.QWidget):

    lightTypes = {
        "Point Light": pm.pointLight,
        "Spot Light": pm.spotLight,
        "Directional Light": pm.directionalLight,
        # partial lets you store the aruments with the function to call later
        # this is done because you cant just give the function name for Area Light
        "Area Light": partial(pm.shadingNode, 'areaLight', asLight=True),
        "Volume Light": partial(pm.shadingNode, 'volumeLight', asLight=True)
    }

# change doc to False to turn off docking to window tab
    def __init__(self, dock=True):
        if dock:
            parent = getDock()
        else:
            deleteDock()
            
            # try to delete, if dosent exist, logg it.
            try:
                pm.deleteUI('lightingManager')
            except:
                logger.debug('No prevouis UI exists')

            parent = QtWidgets.QDialog(parent=getMayaMainWindow())
            parent.setObjectName('lightingManager')
            parent.setWindowTitle('Lighting Manager')
            layout = QtWidgets.QVBoxLayout(parent)

        super(LightManager, self).__init__(parent=parent)
       
        self.buildUI()
        self.populate()

        self.parent().layout().addWidget(self)
        if not dock:
            parent.show()

# checks to see what lights are already there
    def populate(self):
        while self.scrollLayout.count():
            widget = self.scrollLayout.takeAt(0).widget()
            if widget: 
                widget.setVisible(False)
                widget.deleteLater()
        
        for light in pm.ls(type=["areaLight", "spotLight", "pointLight", "directionalLight", "volumeLight"]):
            self.addLight(light)

    def buildUI(self):
        layout = QtWidgets.QGridLayout(self)

        self.lightTypeCB = QtWidgets.QComboBox()
        # .sorted list the library in alphabetical order
        for lightType in sorted(self.lightTypes):
            self.lightTypeCB.addItem(lightType)
        # the two digits equal row and column for the widget
        layout.addWidget(self.lightTypeCB, 0, 0, 1, 2)

        createBtn = QtWidgets.QPushButton('Create')
        createBtn.clicked.connect(self.createLight)
        layout.addWidget(createBtn, 0, 2)

        scrollWidget = QtWidgets.QWidget()
        scrollWidget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.scrollLayout = QtWidgets.QVBoxLayout(scrollWidget)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(scrollWidget)
        # add to row 1, at colmn 0, take 1 row, and 2 columns
        layout.addWidget(scrollArea, 1, 0, 1, 3)

        saveBtn = QtWidgets.QPushButton('Save')
        saveBtn.clicked.connect(self.saveLights)
        layout.addWidget(saveBtn, 2, 0)

        importBtn = QtWidgets.QPushButton('Import')
        importBtn.clicked.connect(self.importLights)
        layout.addWidget(importBtn, 2, 1)

        refreshBtn = QtWidgets.QPushButton('Refresh')
        refreshBtn.clicked.connect(self.populate)
        layout.addWidget(refreshBtn, 2, 2)

    def saveLights(self):
        properties = {}

        for lightWidget in self.findChildren(LightWidget):
            light = lightWidget.light
            transform = light.getTransform()

            properties[str(transform)] = {
                'translate': list(transform.translate.get()),
                'rotation': list(transform.rotate.get()),
                'lightType': pm.objectType(light),
                'intensity': light.intensity.get(),
                'color': light.color.get()
            }

        directory = os.path.join( pm.internalVar(userAppDir=True), 'lightManager' )
        if not os.path.exists(directory):
            os.mkdir(directory)

        # give us month and day in date
        lightFile = os.path.join(directory, 'lightFile_%s.json' % time.strftime('%m%d'))
        with open(lightFile, 'w') as f:
            json.dump(properties, f, indent=4)

        logger.info('Saving file to %s' % lightFile)

    def importLights(self):
        pass

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

    onSolo = Signal(bool)

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

        intensity = QtWidgets.QSlider(Qt.QtCore.Qt.Horizontal)
        intensity.setMinimum(1)
        intensity.setMinimum(1000)
        intensity.setValue(self.light.intensity.get())
        intensity.valueChanged.connect(lambda val: self.light.intensity.set(val))
        layout.addWidget(intensity, 1, 0, 1, 2)

        self.colorBtn = QtWidgets.QPushButton()
        self.colorBtn.setMaximumWidth(20)
        self.colorBtn.setMaximumHeight(20)
        self.setButtonColor()
        self.colorBtn.clicked.connect(self.setColor)
        layout.addWidget(self.colorBtn, 1, 2)

    def setButtonColor(self, color=None):
        if not color:
            color = self.light.color.get()
        assert len(color) == 3, "You must provide a list of 3 colors"

        r,g,b = [c*255 for c in color]

        self.colorBtn.setStyleSheet('background-color: rgba(%s, %s, %s, 1.0)' % (r,g,b))

    def setColor(self):
        lightColor = self.light.color.get()
        color = pm.colorEditor(rgbValue=lightColor)
        
        r,g,b,a = [float(c) for c in color.split()]
        color = (r,g,b)

        self.light.color.set(color)
        self.setButtonColor(color)

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

