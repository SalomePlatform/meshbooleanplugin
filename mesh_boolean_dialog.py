# -*- coding: utf-8 -*-
# Copyright (C) 2007-2024  CEA, EDF
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

import os
import logging
import platform
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import QMessageBox
import salome
from salome_utils import verbose, logger, positionVerbosityOfLogger
from salome.smesh import smeshBuilder
import SalomePyQt
from meshbooleanplugin.MyPlugDialog_ui import Ui_MyPlugDialog
from meshbooleanplugin.mesh_boolean_api import BooleanMeshAlgorithm, booleanOperation, resetCounter
from qtsalome import *

salome.salome_init()
smesh = smeshBuilder.New()
sgPyQt=SalomePyQt.SalomePyQt()

study_name = salome.myStudy.Name
translate=QCoreApplication.translate

#To show messages of error without modifying the script
debug_plugin = os.getenv("DEBUG_PLUGIN")
if debug_plugin or verbose():
  positionVerbosityOfLogger(logging.DEBUG)
  logger.debug("Initial study name : %s" , study_name)

OPERATOR_DICT = { 'Union' : 0, 'Intersection' : 1, 'Difference' : 2 }
LICENSE_DICT = { BooleanMeshAlgorithm.CGAL : 'GPL and LGPL',
                BooleanMeshAlgorithm.IGL  : 'MPL2',
                BooleanMeshAlgorithm.VTK  : 'BSD-3',
                BooleanMeshAlgorithm.IRMB : 'MIT',
                BooleanMeshAlgorithm.CORK : 'LGPL',
                BooleanMeshAlgorithm.MCUT : 'GPL and commercial'
              }

def updateStudy():
  """ Updates the study state and resets counter if the study changed """

  global study_name
  salome.salome_init()

  if debug_plugin or verbose:
    logger.debug("salome.hasDesktop: %s", salome.hasDesktop())
    if salome.sg:
      logger.debug("salome.sg.hasDesktop(): %s", salome.sg.hasDesktop())
    logger.debug("salome.myStudy.Name: %s", salome.myStudy.Name)
    logger.debug("Current study name: %s", study_name)

  if salome.myStudy.Name != study_name:
    logger.debug("Study name changed, calling resetCounter")
    study_name = salome.myStudy.Name
    resetCounter()

class Worker(QObject):
  """ Worker class to handle boolean computation in a thread """
  finished = pyqtSignal(object)
  error = pyqtSignal(str)

  def __init__(self, algo, operator, mesh_left, mesh_right):
    super(Worker, self).__init__()
    self.algo=algo
    self.operator= operator
    self.mesh_right= mesh_right
    self.mesh_left= mesh_left
    self._isRunning= True
    self.process = None

  def task(self):
    """ Execution task for the thread """

    logger.debug("start worker.task")
    try:
      logger.debug("try worker.task")
      if not self._isRunning:
        return
      logger.debug("before runAlgo")
      process = booleanOperation(self.operator, self.mesh_left, self.mesh_right, self.algo, worker=self)
      # using directly the booleanOperation function that takes care of everything ( runalgo and tmpfile)
      logger.debug("in worker.task, self.process: %s", self.process)
      # check if there is a process to call wait
      if self._isRunning:
        self.finished.emit(self.process)
    except Exception as e: # pylint: disable=broad-exception-caught
      if self._isRunning:
        self.error.emit(str(e))

  # stop method to kill the process with the cancel button
  def stop(self):
    """ Terminates the running process """

    logger.debug("in worker.stop()")
    self._isRunning= False
    if self.process is not None:
      logger.debug("self.process is not None => Killing process")
      try:
        self.process.kill()
        logger.debug("Process killed")
      except Exception as e: # pylint: disable=broad-exception-caught
        logger.debug(f"Error killing process:{e}")
    logger.debug("worker.stop() end")

class MeshBooleanDialog(Ui_MyPlugDialog,QWidget):
  """
  Main UI dialog
  """
  def __init__(self):
    global study_name
    QWidget.__init__(self)
    self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
    self.worker = None
    self.setupUi(self)
    self.connecterSignaux()
    self.commande=""

    self.__selectedMesh_L=None
    self.__selectedMesh_R=None
    self.meshIn_L=""
    self.isFile_L=False
    self.meshIn_R=""
    self.isFile_R=False
    self.operator=""
    _translate = QtCore.QCoreApplication.translate
    self.label_summup.setText(_translate("MyPlugDialog", ""))

    # complex with QResources: not used
    # The icon are supposed to be located in the $SMESH_ROOT_DIR/share/salome/resources/smesh folder,
    # other solution could be in the same folder than this python module file:
    # iconfolder=os.path.dirname(os.path.abspath(__file__))

    self.iconfolder=os.path.join(os.environ["SMESH_ROOT_DIR"], "share", "salome", "resources", "smesh")
    icon = QIcon()
    icon.addFile(os.path.join(self.iconfolder,"select1.png"))
    self.PB_MeshSmesh_L.setIcon(icon)
    self.PB_MeshSmesh_L.setToolTip("source mesh from Salome Object Browser")
    self.PB_MeshSmesh_R.setIcon(icon)
    self.PB_MeshSmesh_R.setToolTip("source mesh from Salome Object Browser")
    icon = QIcon()
    icon.addFile(os.path.join(self.iconfolder,"open.png"))
    self.PB_MeshFile_L.setIcon(icon)
    self.PB_MeshFile_L.setToolTip("source mesh from a file in disk")
    self.PB_MeshFile_R.setIcon(icon)
    self.PB_MeshFile_R.setToolTip("source mesh from a file in disk")
    self.resize(800, 600)

    self.myWindow = None

    self.computing = False

  def connecterSignaux(self) :
    """ Connects UI signals """
    self.PB_Close.clicked.connect(self.onPBClosePressed)
    self.PB_Cancel.clicked.connect(self.onPBCancelPressed)
    self.PB_Help.clicked.connect(self.onPBHelpPressed)
    self.PB_Compute.clicked.connect(self.onPBComputePressed)

    self.LE_MeshFile_L.returnPressed.connect(lambda : self.onMeshFileNameSelected("L"))
    self.LE_MeshSmesh_L.returnPressed.connect(lambda : self.onMeshSmeshNameChanged("L"))
    self.PB_MeshFile_L.clicked.connect(lambda _: self.onPBMeshFilePressed("L"))
    self.PB_MeshSmesh_L.clicked.connect(lambda _: self.onPBMeshSmeshPressed("L"))
    self.LE_MeshFile_R.returnPressed.connect(lambda : self.onMeshFileNameSelected("R"))
    self.LE_MeshSmesh_R.returnPressed.connect(lambda : self.onMeshSmeshNameChanged("R"))
    self.PB_MeshFile_R.clicked.connect(lambda _: self.onPBMeshFilePressed("R"))
    self.PB_MeshSmesh_R.clicked.connect(lambda _: self.onPBMeshSmeshPressed("R"))

    self.COB_Operator.currentIndexChanged.connect(self.displayOperatorLabel)
    self.COB_Engine.currentIndexChanged.connect(self.displayEngineLabel)

  def displaySummupLabel(self):
    """ Updates the summary label with selected meshes and operator """
    _translate = QtCore.QCoreApplication.translate
    if self.meshIn_L == "" or self.meshIn_R == "":
      self.label_summup.setText(_translate("MyPlugDialog", ""))
      return
    symbol = ''
    if self.operator.lower() == 'union':
      symbol = '\u222A'
    elif self.operator.lower() == 'intersection':
      symbol = '\u2229'
    else:
      symbol = '\u2216'

    left_name = str(self.LE_MeshSmesh_L.text())
    if self.isFile_L:
      left_name = os.path.splitext(os.path.basename(str(self.LE_MeshFile_L.text())))[0]
    right_name = str(self.LE_MeshSmesh_R.text())
    if self.isFile_R:
      right_name = os.path.splitext(os.path.basename(str(self.LE_MeshFile_R.text())))[0]

    engine = self.getCurrentAlgorithm().value
    if engine == BooleanMeshAlgorithm.IRMB.value:
      engine = "IRMB" # prettier display

    self.label_summup.setText(_translate("MyPlugDialog", f"({engine}) : {left_name} {symbol} {right_name}"))

  def error_popup(self, title, e):
    """ Displays critical error message box """

    QMessageBox.critical(self, title, str(e))
    return False

  def getCurrentAlgorithm(self):
    """ Returns the currently selected algorithm """
    for algo in BooleanMeshAlgorithm:
      if algo.value == self.COB_Engine.currentText() :
        return algo
    if platform.system() == "Windows" :
      return BooleanMeshAlgorithm.IGL
    return BooleanMeshAlgorithm.CGAL

  def displayOperatorLabel(self):
    """ Updates license information text """
    _translate = QtCore.QCoreApplication.translate
    for key, val in OPERATOR_DICT.items():
      if self.COB_Operator.currentIndex() == val:
        self.label_Operator.setText(_translate("MyPlugDialog", f"Compute the {key.lower()} of the two meshes selected."))

  def displayEngineLabel(self):
    _translate = QtCore.QCoreApplication.translate
    self.label_Engine.setText(_translate("MyPlugDialog", f"This engine is used under the {LICENSE_DICT[self.getCurrentAlgorithm()]} license."))

  def onPBHelpPressed(self):
    QMessageBox.about(self, "About this boolean mesh operation tool",
            """
This tool allows you to apply boolean
operators to your meshes. You can fill
the 'Left mesh' and the 'Right mesh' fields,
choose an operator and an engine and
compute the result.

For each engine, you can access a piece of
information about its performances with the
selected operator, measuring the metric
that you selected.
            """)

  def setCursorBusy(self):
    QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
    self.repaint()

  def restoreCursor(self):
    QApplication.restoreOverrideCursor()
    self.repaint()
    sgPyQt.processEvents()

# onComputeFinished fonction called with signals afterwards
  def onComputeFinished(self, result_mesh):
    print("Computation finished")
    self.computing= False
    self.updateButton()
    self.restoreCursor()

    if result_mesh: # we now refresh the GUI here (no longer need of the function loadResult)
      if salome.sg.hasDesktop():
        salome.sg.updateObjBrowser()
        QMessageBox.about(self,"Compute", "Computation successfully finished")
    else:
      self.error_popup("Error", "Computation failed")

    self.worker.deleteLater()

# updateButton fonction to enable the 'Cancel' button and disable the 'Compute' one (and vice-versa)
  def updateButton(self):
    """ Toggles state between compute and cancel buttons """
    if self.computing:
      self.PB_Compute.setEnabled(False)
      self.PB_Cancel.setEnabled(True)
    else:
      self.PB_Compute.setEnabled(True)
      self.PB_Cancel.setEnabled(False)
    # Forcing the change to happen in SALOME
    sgPyQt.processEvents()


  def onPBCancelPressed(self):
    """ Handles user request to cancel the computation """
    if self.worker is None or not self.computing:
      return

    logger.debug("Cancel called by user")
    self.worker.stop()
    self.thread.quit()
    self.computing=False
    self.updateButton()

    if salome.sg.hasDesktop():
      salome.sg.updateObjBrowser()
      self.restoreCursor()
      QMessageBox.about(self, "Compute","Computation canceled by user")
    else:
      print("Computation canceled by user")

  def onPBComputePressed(self):
    """ Initializes and starts the computation thread """
    logger.debug("Compute  called by user")

    mesh_l = self.__selectedMesh_L if self.__selectedMesh_L else self.meshIn_L
    mesh_r = self.__selectedMesh_R if self.__selectedMesh_R else self.meshIn_R

    if not mesh_l or not mesh_r:
      return self.error_popup("Mesh", "Select an input mesh")

    self.setCursorBusy()

    self.thread = QThread()
    self.operator = self.COB_Operator.currentText() #stock the operator correctly to name the files after
    self.worker = Worker(self.getCurrentAlgorithm(),self.operator.lower(),mesh_l, mesh_r)

    self.worker.moveToThread(self.thread)

    self.thread.started.connect(self.worker.task)
    self.worker.finished.connect(self.onComputeFinished)
    self.worker.finished.connect(self.thread.quit)
    self.worker.error.connect(lambda e: self.error_popup("Computation error", e))
    self.thread.finished.connect(self.thread.deleteLater)
#   start the thread(the computation)
    self.thread.start()

    self.computing=True
#   unlock the cancel button
    self.updateButton()

  def onPBClosePressed(self):
    self.close()

  def onPBMeshFilePressed(self, zone):
    """zone = L or R"""
    filter_string = "All mesh formats supported (*.obj *.off *.mesh *.med *.stl);;All Files (*)"

    if zone == 'L':
      fd = QFileDialog(self, "select an existing mesh file", self.LE_MeshFile_L.text(), filter_string)
    else :
      fd = QFileDialog(self, "select an existing mesh file", self.LE_MeshFile_R.text(), filter_string)
    if fd.exec_():
      infile = fd.selectedFiles()[0]
      if zone == 'L':
        self.LE_MeshFile_L.setText(infile)
        self.meshIn_L=str(infile)
        self.isFile_L=True
      else:
        self.LE_MeshFile_R.setText(infile)
        self.meshIn_R=str(infile)
        self.isFile_R=True
      #self.currentName = os.path.splitext(os.path.basename(self.fichierIn))[0]
      if zone == 'L':
        self.LE_MeshSmesh_L.setText("")
        self.__selectedMesh_L=None
      else:
        self.LE_MeshSmesh_R.setText("")
        self.__selectedMesh_R=None

    self.displaySummupLabel()

  def onPBMeshSmeshPressed(self, zone):
    """zone = L or R"""
    from omniORB import CORBA
    from salome.smesh.smeshstudytools import SMeshStudyTools
    from salome.gui import helper as guihelper

    # mySObject, myEntry = guihelper.getSObjectSelected()
    updateStudy()
    myEntry = salome.sg.getSelected(0)
    if not myEntry:
      logger.debug("No selection found in object browser")
      self.error_popup("Selection error", "Please select a mesh in the object browser first")
      return
    try:
      mySObject = salome.IDToSObject(myEntry)
    except Exception as e:
      logger.error("Failed to get SObject from entry %s: %s", myEntry, e)
      return

    if CORBA.is_nil(mySObject) or mySObject is None:
      QMessageBox.critical(self, "Mesh", "select an input mesh")
      return
    self.smeshStudyTool = SMeshStudyTools()
    if zone == "L":
      try:
        self.__selectedMesh_L = self.smeshStudyTool.getMeshObjectFromSObject(mySObject)
      except:
        QMessageBox.critical(self, "Mesh", "select an input mesh")
        return
      if CORBA.is_nil(self.__selectedMesh_L):
        QMessageBox.critical(self, "Mesh", "select an input mesh")
        return
    else:
      try:
        self.__selectedMesh_R = self.smeshStudyTool.getMeshObjectFromSObject(mySObject)
      except:
        QMessageBox.critical(self, "Mesh", "select an input mesh")
        return
      if CORBA.is_nil(self.__selectedMesh_R):
        QMessageBox.critical(self, "Mesh", "select an input mesh")
        return
    myName = mySObject.GetName()

    # set mesh name to input field
    # only if it differs from the other mesh
    if zone == 'L' and myName != self.meshIn_R:
      #self.currentName = myName
      self.meshIn_L=myName
      self.LE_MeshSmesh_L.setText(myName)
      self.LE_MeshFile_L.setText("")
      self.isFile_L = False
    elif zone == 'R' and myName != self.meshIn_L:
      #self.currentName = myName
      self.meshIn_R=myName
      self.LE_MeshSmesh_R.setText(myName)
      self.LE_MeshFile_R.setText("")
      self.isFile_R = False

    self.displaySummupLabel()

  def onMeshFileNameSelected(self, zone):
    """zone = L or R"""
    if zone == 'L':
      self.meshIn_L=str(self.LE_MeshFile_L.text())
      self.isFile_L=False
      if os.path.exists(self.meshIn_L):
        self.__selectedMesh_L=None
        self.LE_MeshSmesh_L.setText("")
        #self.currentname = os.path.basename(self.fichierIn)
        self.displaySummupLabel()
        return
    else:
      self.meshIn_R=str(self.LE_MeshFile_R.text())
      self.isFile_R=False
      if os.path.exists(self.meshIn_R):
        self.__selectedMesh_R=None
        self.LE_MeshSmesh_R.setText("")
        #self.currentname = os.path.basename(self.fichierIn)
        self.displaySummupLabel()
        return
    QMessageBox.warning(self, "Mesh file", "File doesn't exist")


  def onMeshSmeshNameChanged(self, zone):
    """only change by GUI mouse selection, otherwise clear // zone = L or R"""
    if zone == 'L':
      self.__selectedMesh_L = None
      self.LE_MeshSmesh_L.setText("")
      self.meshIn_L = ""
    else:
      self.__selectedMesh_R = None
      self.LE_MeshSmesh_R.setText("")
      self.meshIn_R = ""
    self.displaySummupLabel()
    return

def getDialog():
  """
  This function returns a new instance of the plugin dialog everytime it is called.
  An attribute in __init__ handles the cleanup.
  """
  return MeshBooleanDialog()  # To destroy the window everytime we close it
                              # no need for global variable, more proper and more simplified
