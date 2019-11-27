import json
import os
import Qt
import time
from Qt import QtWidgets, QtCore, QtGui
import logging

"""

INSTALLATION:

Place python files in Maya"year" scripts folder.
To run script, TYPE INTO MAYA PYTHON CONSOLE:

import lightingManager
reload(lightingManager)

lightingManager.LightingManager(dock=False)

"""

logging.basicConfig()
logger = logging.getLogger('LightingManager')
# switch DEBUG to INFO when publishing.
logger.setLevel(logging.INFO)

# checks Qt binding
if Qt.__binding__.startswith('PyQt'):
    # If using PyQt4 or PyQt5 we need to import sip
    logger.debug('Using sip')
    from sip import wrapinstance as wrapInstance
    from Qt.QtCore import pyqtSignal as Signal
elif Qt.__binding__ == 'PySide':
    # If using PySide (Maya 2016 and earlier), user needs shiboken instead
    logger.debug('Using shiboken')
    from shiboken import wrapInstance
    from Qt.QtCore import Signal
else:
    # PySide2(Maya 2017 and higher) uses shiboken2
    logger.debug('Using shiboken2')
    from shiboken2 import wrapInstance
    from Qt.QtCore import Signal

from maya import OpenMayaUI as omui
import pymel.core as pm

# functional tools library, partial is for craeting temporary functions
from functools import partial

# Basic contoller for lights
class LightWidget(QtWidgets.QWidget):

    # solo signal created for connecting to other Qt objects
    onSolo = Signal(bool)

    def __init__(self, light):

        super(LightWidget, self).__init__()

        # If light is a string, convert it to a PyMel object 
        if isinstance(light, basestring):
            logger.debug('Converting node to a PyNode')
            light = pm.PyNode(light)

        # if transform make it a light shape, 
        if isinstance(light, pm.nodetypes.Transform):
            light = light.getShape()

        self.light = light
        self.buildUI()

    # THE UI 
    def buildUI(self):
        layout = QtWidgets.QGridLayout(self)

        self.name = name = QtWidgets.QCheckBox(str(self.light.getTransform()))
        name.setChecked(self.light.visibility.get())
        
        # lambdas are one time use functions. 
        name.toggled.connect(lambda val: self.light.visibility.set(val))
        # (row 0, column 0)
        layout.addWidget(name, 0, 0)

        # button to solo the light
        solo = QtWidgets.QPushButton('Solo')
        solo.setCheckable(True)
        solo.toggled.connect(lambda val: self.onSolo.emit(val))
        layout.addWidget(solo, 0, 1)

        # delete light button 
        delete = QtWidgets.QPushButton('X')
        delete.clicked.connect(self.deleteLight)
        delete.setMaximumWidth(20)
        layout.addWidget(delete, 0, 2)

        # slider for intensity of light
        intensity = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        intensity.setMinimum(1)
        intensity.setMaximum(1000)
        # set its current value based on the intensity of the light itself
        intensity.setValue(self.light.intensity.get())
        intensity.valueChanged.connect(lambda val: self.light.intensity.set(val))
        # row 1, column 2, take 1 row and 2 columns of space.
        layout.addWidget(intensity, 1, 0, 1, 2)

        # color light button 
        self.colorBtn = QtWidgets.QPushButton()
        self.colorBtn.setMaximumWidth(20)
        self.colorBtn.setMaximumHeight(20)
        self.setButtonColor()
        self.colorBtn.clicked.connect(self.setColor)
        layout.addWidget(self.colorBtn, 1, 2)

        # widget should never be larger than the maximum space it needs
        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

    def disableLight(self, val):
        # takes a value, converts it to bool, then sets checkbox to value
        self.name.setChecked(not bool(val))

    def deleteLight(self):
        # set parent to Nothing, will remove it from the manager UI and tells Qt to drop it
        self.setParent(None)
        # awkward period of time before Qt deletes it after clicking X..
        # So mark its visibility to False
        self.setVisible(False)
        # delete it later just in case it hasn't gotten the hint yet
        self.deleteLater()
        pm.delete(self.light.getTransform())

    def setColor(self):
        lightColor = self.light.color.get()
        color = pm.colorEditor(rgbValue=lightColor)

        # it gives back a string instead of a list of numbers.
        # split the string, then convert it to floats
        r, g, b, a = [float(c) for c in color.split()]

        color = (r, g, b)
        self.light.color.set(color)
        self.setButtonColor(color)

    def setButtonColor(self, color=None):

        # If no color, use color from the light
        if not color:
            color = self.light.color.get()

        assert len(color) == 3, "You must provide a list of 3 colors"

        # multiply members of color by 255 to get the correct number
        r, g, b = [c * 255 for c in color]
        self.colorBtn.setStyleSheet('background-color: rgba(%s, %s, %s, 1.0);' % (r, g, b))

# Main Lighting Manager
class LightingManager(QtWidgets.QWidget):

    lightTypes = {
        "Point Light": pm.pointLight,
        "Spot Light": pm.spotLight,
        "Area Light": partial(pm.shadingNode, 'areaLight', asLight=True),
        "Directional Light": pm.directionalLight,
        "Volume Light": partial(pm.shadingNode, 'volumeLight', asLight=True)
    }

# Set Dock to True if you want it to dock 
    def __init__(self, dock=False):
        
        if dock:
            parent = getDock()
        else:
            deleteDock()
            try:
                pm.deleteUI('lightingManager')
            except:
                logger.debug('No previous UI exists')
            parent = QtWidgets.QDialog(parent=getMayaMainWindow())
            parent.setObjectName('lightingManager')
            parent.setWindowTitle('Lighting Manager')
            dlgLayout = QtWidgets.QVBoxLayout(parent)

        super(LightingManager, self).__init__(parent=parent)

        self.buildUI()
        self.populate()
        self.parent().layout().addWidget(self)

        if not dock:
            parent.show()

    def buildUI(self):
        layout = QtWidgets.QGridLayout(self)

        # Comboboxes are essentially dropdown selectionwidgets
        self.lightTypeCB = QtWidgets.QComboBox()
        for lightType in sorted(self.lightTypes):
            self.lightTypeCB.addItem(lightType)
        # take 1 row, and two columns worth of space
        layout.addWidget(self.lightTypeCB, 0, 0, 1, 2)

        # button for creating chosen light
        createBtn = QtWidgets.QPushButton('Create')
        createBtn.clicked.connect(self.createLight)
        layout.addWidget(createBtn, 0, 2)

        # scroll container widget
        scrollWidget = QtWidgets.QWidget()
        scrollWidget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.scrollLayout = QtWidgets.QVBoxLayout(scrollWidget)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(scrollWidget)
        layout.addWidget(scrollArea, 1, 0, 1, 3)

        # Save button for lights setup
        saveBtn = QtWidgets.QPushButton('Save')
        saveBtn.clicked.connect(self.saveLights)
        layout.addWidget(saveBtn, 2, 0)

        # import button for lights
        importBtn = QtWidgets.QPushButton('Import')
        importBtn.clicked.connect(self.importLights)
        layout.addWidget(importBtn, 2, 1)

        # Refresh button 
        refreshBtn = QtWidgets.QPushButton('Refresh')
        refreshBtn.clicked.connect(self.refresh)
        layout.addWidget(refreshBtn, 2, 2)

    def refresh(self):
 
        # while scrollLayout.count() gives any Truth-y value, run logic
        while self.scrollLayout.count():
            widget = self.scrollLayout.takeAt(0).widget()
           
            if widget:
                # Set visibility to False because there is a period where it will still be alive
                widget.setVisible(False)
                # kill the widget when it can
                widget.deleteLater()

        self.populate()

    def populate(self):
        for light in pm.ls(type=["areaLight", "spotLight", "pointLight", "directionalLight", "volumeLight"]):
            self.addLight(light)

    # save lights to JSON file
    def saveLights(self):
        properties = {}

        for lightWidget in self.findChildren(LightWidget):
            light = lightWidget.light
            transform = light.getTransform()

            # add it to the dictionary.
            properties[str(transform)] = {
                'translate': list(transform.translate.get()),
                'rotation': list(transform.rotate.get()),
                'lightType': pm.objectType(light),
                'intensity': light.intensity.get(),
                'color': light.color.get()
            }

        # fetch the light manager directory to save in
        directory = self.getDirectory()

        # construct name of the lightFile to save
        # %m%d%S = (month/day/secounds)
        lightFile = os.path.join(directory, 'lightFile_%s.json' % time.strftime('%m%d%S'))

        # open file to write
        with open(lightFile, 'w') as f:
            json.dump(properties, f, indent=4)

        logger.info('Saving file to %s' % lightFile)

    def getDirectory(self):
        #  gives us back the name of our library directory and create it if it doesn't exist
        directory = os.path.join(pm.internalVar(userAppDir=True), 'lightManager')
        if not os.path.exists(directory):
            os.mkdir(directory)
        return directory

    def importLights(self):
        directory = self.getDirectory()

        fileName = QtWidgets.QFileDialog.getOpenFileName(self, "Light Browser", directory)

        # open fileName in read mode
        with open(fileName[0], 'r') as f:
            properties = json.load(f)

        for light, info in properties.items():

            lightType = info.get('lightType')
            for lt in self.lightTypes:
                # the light type for Point Light is pointLight, convert Point Light to pointLight and then compare
                if ('%sLight' % lt.split()[0].lower()) == lightType:
                    # If match found, break out
                    break
            else:
                logger.info('Cannot find a corresponding light type for %s (%s)' % (light, lightType))
                continue

            light = self.createLight(lightType=lt)

            light.intensity.set(info.get('intensity'))
            light.color.set(info.get('color'))
            transform = light.getTransform()
            transform.translate.set(info.get('translate'))
            transform.rotate.set(info.get('rotation'))

        self.populate()

    def createLight(self, lightType=None, add=True):
        # get text from the combobox if no light is given
        if not lightType:
            lightType = self.lightTypeCB.currentText()

        # look up lightTypes dictionary to find function to call
        func = self.lightTypes[lightType]

        light = func()
        # pass to addLight if the method has been told to add it
        if add:
            self.addLight(light)

        return light

  # create a LightWidget for light and add it to the UI
    def addLight(self, light):
        widget = LightWidget(light)

        # connect the onSolo signal from the widget to isolate method
        widget.onSolo.connect(self.isolate)
        self.scrollLayout.addWidget(widget)

  # function for isolateing a single light
    def isolate(self, val):

        lightWidgets = self.findChildren(LightWidget)
        for widget in lightWidgets:
            if widget != self.sender():
                widget.disableLight(val)


def getMayaMainWindow():
  
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr


def getDock(name='LightingManagerDock'):
   
    # delete any conflicting docks
    deleteDock(name)
    ctrl = pm.workspaceControl(name, dockToMainWindow=('right', 1), label="Lighting Manager")
    qtCtrl = omui.MQtUtil_findControl(ctrl)

    # wrapInstance used to convert it to something Python can understand, in this case a QWidget
    ptr = wrapInstance(long(qtCtrl), QtWidgets.QWidget)

    return ptr


def deleteDock(name='LightingManagerDock'):
    
    # workspaceControl used to see if dock exists
    if pm.workspaceControl(name, query=True, exists=True):
        pm.deleteUI(name)
