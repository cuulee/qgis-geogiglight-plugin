# -*- coding: utf-8 -*-

"""
***************************************************************************
    plugin.py
    ---------------------
    Date                 : March 2016
    Copyright            : (C) 2016 Boundless, http://boundlessgeo.com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
from builtins import object

__author__ = 'Victor Olaya'
__date__ = 'March 2016'
__copyright__ = '(C) 2016 Boundless, http://boundlessgeo.com'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect
import webbrowser

from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolButton, QMessageBox

from qgis.core import QgsMapLayerRegistry, QgsApplication

from geogig import config
from geogig.gui.dialogs.configdialog import ConfigDialog
from geogig.gui.dialogs.navigatordialog import NavigatorDialog
from geogig.gui.dialogs.importdialog import ImportDialog
from geogig.gui.dialogs.navigatordialog import navigatorInstance

from geogig.layeractions import setAsRepoLayer, setAsNonRepoLayer, removeLayerActions

from geogig.tools.utils import deleteTempFolder
from geogig.tools.infotool import MapToolGeoGigInfo
from geogig.tools.layertracking import removeNonexistentTrackedLayers, readTrackedLayers, isRepoLayer

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

def trackLayer(layer):
    if isRepoLayer(layer):
        setAsRepoLayer(layer)
    else:
        setAsNonRepoLayer(layer)

def layerRemoved(layer):
    if QgsMapLayerRegistry is not None:
        layer = QgsMapLayerRegistry.instance().mapLayer(layer)
        removeLayerActions(layer)

class GeoGigPlugin(object):

    def __init__(self, iface):
        self.iface = iface
        config.iface = iface

        config.initConfigParams()

        layers = list(QgsMapLayerRegistry.instance().mapLayers().values())
        for layer in layers:
            trackLayer(layer)
        try:
            from qgistester.tests import addTestModule
            from geogig.tests import testplugin
            addTestModule(testplugin, "GeoGig Light")
        except Exception as e:
            pass

        QSettings().setValue("/qgis/walForSqlite3", False)

    def unload(self):
        navigatorInstance.setVisible(False)
        try:
            QgsMapLayerRegistry.instance().layerWasAdded.disconnect(trackLayer)
            QgsMapLayerRegistry.instance().layerRemoved.disconnect(layerRemoved)
        except:
            pass
        self.menu.deleteLater()
        self.toolButton.deleteLater()
        layers = list(QgsMapLayerRegistry.instance().mapLayers().values())
        for layer in layers:
            removeLayerActions(layer)
        removeNonexistentTrackedLayers()
        deleteTempFolder()

        try:
            from qgistester.tests import removeTestModule
            from geogig.tests import testplugin
            removeTestModule(testplugin, "GeoGig Light")
        except Exception as e:
            pass

        try:
            from lessons import removeLessonsFolder
            removeLessonsFolder(folder, "geogig")
        except:
            return

    def initGui(self):
        readTrackedLayers()

        QgsMapLayerRegistry.instance().layerWasAdded.connect(trackLayer)
        QgsMapLayerRegistry.instance().layerRemoved.connect(layerRemoved)

        icon = QIcon(os.path.dirname(__file__) + "/ui/resources/geogig.png")
        self.explorerAction = navigatorInstance.toggleViewAction()
        self.explorerAction.setIcon(icon)
        self.explorerAction.setText("GeoGig Navigator")
        icon = QIcon(os.path.dirname(__file__) + "/ui/resources/config.png")
        self.configAction = QAction(icon, "GeoGig Settings", self.iface.mainWindow())
        self.configAction.triggered.connect(self.openSettings)
        icon = QIcon(os.path.dirname(__file__) + "/ui/resources/identify.png")
        self.toolAction = QAction(icon, "GeoGig Feature Info Tool", self.iface.mainWindow())
        self.toolAction.setCheckable(True)
        self.toolAction.triggered.connect(self.setTool)
        helpIcon = QgsApplication.getThemeIcon('/mActionHelpAPI.png')
        self.helpAction = QAction(helpIcon, "GeoGig Plugin Help", self.iface.mainWindow())
        self.helpAction.setObjectName("GeoGigHelp")
        self.helpAction.triggered.connect(lambda: webbrowser.open_new("file://" + os.path.join(os.path.dirname(__file__), "docs", "html", "index.html")))
        self.menu = QMenu(self.iface.mainWindow())
        self.menu.setTitle("GeoGig")
        self.menu.addAction(self.explorerAction)
        self.menu.addAction(self.toolAction)
        self.menu.addAction(self.configAction)
        self.menu.addAction(self.helpAction)
        bar = self.iface.layerToolBar()
        self.toolButton = QToolButton()
        self.toolButton.setMenu(self.menu)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButton.setDefaultAction(self.explorerAction)
        useMainMenu = config.getConfigValue(config.GENERAL, config.USE_MAIN_MENUBAR)
        bar.addWidget(self.toolButton)
        if useMainMenu:
            menuBar = self.iface.mainWindow().menuBar()
            menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)
        else:
            self.iface.addPluginToMenu(u"&GeoGig", self.explorerAction)
            self.iface.addPluginToMenu(u"&GeoGig", self.configAction)
            self.iface.addPluginToMenu(u"&GeoGig", self.toolAction)

        self.mapTool = MapToolGeoGigInfo(self.iface.mapCanvas())
        #This crashes QGIS, so we comment it out until finding a solution
        #self.mapTool.setAction(self.toolAction)

        self.iface.addDockWidget(Qt.RightDockWidgetArea, navigatorInstance)

        try:
            from lessons import addLessonsFolder
            folder = os.path.join(os.path.dirname(__file__), "_lessons")
            addLessonsFolder(folder, "geogig")
        except Exception as e:
            pass

    def setWarning(self, msg):
        QMessageBox.warning(None, 'Could not complete GeoGig command',
                                  msg,
                                  QMessageBox.Ok)

    def setTool(self):
        self.toolAction.setChecked(True)
        self.iface.mapCanvas().setMapTool(self.mapTool)


    def openSettings(self):
        dlg = ConfigDialog()
        dlg.exec_()
