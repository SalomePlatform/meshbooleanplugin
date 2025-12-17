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
import tempfile
import logging
from salome.kernel import salome
from salome.kernel.salome_utils import verbose, logger, positionVerbosityOfLogger
import SalomePyQt
from meshbooleanplugin.MyPlugDialog_ui import Ui_MyPlugDialog
from qtsalome import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import QMessageBox

from meshbooleanplugin.mesh_boolean_utils import meshIOConvert
import platform
from meshbooleanplugin.mesh_boolean_api import runAlgo, BooleanMeshAlgorithm
from salome.smesh import smeshBuilder
smesh = smeshBuilder.New()

sgPyQt=SalomePyQt.SalomePyQt()

translate=QCoreApplication.translate

#To show messages of error without modifying the script
debug_plugin = os.getenv("DEBUG_PLUGIN")
if debug_plugin or verbose():
  positionVerbosityOfLogger(logging.DEBUG)

OPERATOR_DICT = { 'Union' : 0, 'Intersection' : 1, 'Difference' : 2 }
LICENSE_DICT = { BooleanMeshAlgorithm.CGAL : 'GPL and LGPL',
                BooleanMeshAlgorithm.IGL  : 'MPL2',
                BooleanMeshAlgorithm.VTK  : 'BSD-3',
                BooleanMeshAlgorithm.IRMB : 'MIT',
                BooleanMeshAlgorithm.CORK : 'LGPL',
                BooleanMeshAlgorithm.MCUT : 'GPL and commercial'
              }

def getTmpFileName(suffix=None, prefix=None):
  tempdir = tempfile.gettempdir()
  tmp_file = tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, dir=tempdir, delete=False)
  tmp_filename = tmp_file.name
  return tmp_filename


#Worker class for Qthread
class Worker(QObject):
  finished = pyqtSignal(str)
  error = pyqtSignal(str)

  def __init__(self, algo, operator, mesh_left, mesh_right, result_file):
    super(Worker, self).__init__()
    self.algo=algo
    self.operator= operator
    self.mesh_right= mesh_right
    self.mesh_left= mesh_left
    self.result_file= result_file
    self.output_file= None
    self._isRunning= True
    self.process = None
    self.returncode = None

  def task(self):
    logger.debug("start worker.task")
    try:
      logger.debug("try worker.task")
      if not self._isRunning:
        return
      logger.debug("before runAlgo")
      self.process = runAlgo(self.algo, self.operator, self.mesh_left, self.mesh_right, self.result_file)
      logger.debug(f"in worker.task, self.process:{self.process}")
      #check if there is a process to call wait
      if self.process is not None:
        #wait called to wait the end of the process
        logger.debug("before wait")
        self.returncode = self.process.wait()
        logger.debug("after wait")
      if self._isRunning:
        self.finished.emit(self.result_file)
    except Exception as e:
      self.error.emit(str(e))

  #stop method to kill the process with the cancel button
  def stop(self):
    logger.debug("in worker.stop()")
    self._isRunning= False
    if self.process is not None:
      logger.debug("self.process is not None => Killing process")
      try:
        self.process.kill()
        logger.debug("Process killed")
      except Exception as e:
        logger.debug(f"Error killing process:{e}")
    logger.debug("worker.stop() end")

class MeshBooleanDialog(Ui_MyPlugDialog,QWidget):
  """
  """
  def __init__(self):
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
    self.result_file = None

  def connecterSignaux(self) :
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
    QMessageBox.critical(self, title, str(e))
    return False

  def getCurrentAlgorithm(self):
    for algo in BooleanMeshAlgorithm:
      if algo.value == self.COB_Engine.currentText() :
        return algo
    if platform.system() == "Windows" :
      return BooleanMeshAlgorithm.IGL
    return BooleanMeshAlgorithm.CGAL

  def generateObjFromMed(self, zone):
    """zone = L or R"""
    # Get selected mesh or file name
    if zone == "L":
      selectedMesh = self.__selectedMesh_L
      meshIn = self.meshIn_L
    else:
      selectedMesh = self.__selectedMesh_R
      meshIn = self.meshIn_R

    objTmpFileName = getTmpFileName(suffix=".obj", prefix="ForBMC_")
    stlTmpFileName = getTmpFileName(suffix=".stl",prefix="ForBMC_")
    if meshIn[:-3] not in ["obj", "stl"] and selectedMesh is None:
      # if a file is selected, first convert it to stl to get triangles only
      # otherwise meshio convert to obj fails
      meshIOConvert(meshIn, stlTmpFileName)
      meshIn = stlTmpFileName
    elif selectedMesh is not None:
      # export selected mesh to STL
      try:
        selectedMesh.ExportSTL(stlTmpFileName, False) # isascci
      except Exception as e:
        return self.error_popup("Mesh export", e)
      meshIn = stlTmpFileName
    # Convert file to OBJ
    meshIOConvert(meshIn, objTmpFileName)
    if zone == "L":
      self.meshIn_L = objTmpFileName
    else:
      self.meshIn_R = objTmpFileName

  def displayOperatorLabel(self):
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

  def generateInputFiles(self, zone):
    """zone = L or R"""
    self.generateObjFromMed(zone)

  def setCursorBusy(self):
    QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
    self.repaint()

  def restoreCursor(self):
    QApplication.restoreOverrideCursor()
    self.repaint()
    sgPyQt.processEvents()

# onComputeFinished fonction called with signals afterwards
  def onComputeFinished(self):
    print("Computation finished")
    self.loadResult()
    self.computing= False
    self.updateButton()
    self.restoreCursor()

# updateButton fonction to enable the 'Cancel' button and disable the 'Compute' one (and vice-versa)
  def updateButton(self):
    if self.computing:
      self.PB_Compute.setEnabled(False)
      self.PB_Cancel.setEnabled(True)
    else:
      self.PB_Compute.setEnabled(True)
      self.PB_Cancel.setEnabled(False)
    #Forcing the change to happen in SALOME
    sgPyQt.processEvents()


  def onPBCancelPressed(self):
    logger.debug("Cancel called by user")
  # check that there is a process then stop it if there is
    if self.worker is not None:
      print("Process stopped")
      self.worker.stop()
      try:
        self.thread.quit()
        self.thread.wait()
      except Exception as e:
        print(e)
        pass
    self.computing=False
    self.updateButton()

    if salome.sg.hasDesktop():
      salome.sg.updateObjBrowser()
      self.restoreCursor()
      QMessageBox.about(self, "Compute","Computation canceled by user")
    else:
      print("Computation canceled by user")

  def onPBComputePressed(self):
    logger.debug("Compute  called by user")

    if self.meshIn_R=="" or self.meshIn_L=="":
      return self.error_popup("Mesh", "select an input mesh")

    self.setCursorBusy()
    if self.__selectedMesh_L is not None or not self.meshIn_L.endswith(".obj"):
      try:
        self.generateInputFiles("L")
      except Exception as e:
        self.restoreCursor()
        return self.error_popup("Error when converting the left mesh ", e)
    if self.__selectedMesh_R is not None or not self.meshIn_R.endswith(".obj"):
      try:
        self.generateInputFiles("R")
      except Exception as e:
        self.restoreCursor()
        return self.error_popup("Error when converting the right mesh ", e)
    if not os.path.isfile(self.meshIn_L):
      self.restoreCursor()
      return self.error_popup("File", "unable to read mesh in "+str(self.meshIn_L))
    if not os.path.isfile(self.meshIn_R):
      self.restoreCursor()
      return self.error_popup("File", "unable to read mesh in "+str(self.meshIn_R))

    self.result_file = getTmpFileName(suffix=".med",prefix="ForBMC_")

    self.thread = QThread()
    self.operator = self.COB_Operator.currentText() #stock the operator correctly to name the files after
    self.worker = Worker(self.getCurrentAlgorithm(),self.operator.lower(),self.meshIn_L, self.meshIn_R, self.result_file)

    self.worker.moveToThread(self.thread)

    self.thread.started.connect(self.worker.task)
    self.worker.finished.connect(self.onComputeFinished)
    self.worker.finished.connect(self.worker.deleteLater)
    self.worker.finished.connect(self.thread.quit)
    self.thread.finished.connect(self.thread.deleteLater)
    self.worker.error.connect(lambda e: self.error_popup("Computation error", e))
#   start the thread(the computation)
    self.thread.start()

    self.computing=True
#   unlock the cancel button
    self.updateButton()

  def loadResult(self):
    from meshbooleanplugin.mesh_boolean_api import convertAlgorithmResult, importMedToSmesh

    logger.debug(f"return code: {self.worker.returncode}")
    if (self.worker.returncode) != 0:
      self.restoreCursor()
      self.error_popup("Error", "Computation ended in error.")
      return

    #see which algorithm is called to convert the appropriate result into a .med file
    algo = self.getCurrentAlgorithm()
    #use the convertAlgorithmResult function from the API to avoid repeating the same code
    convertAlgorithmResult(algo, self.result_file)

    try:
      #Use the importMedToSmesh function from the API
      outputMesh = importMedToSmesh(self.result_file, operator_name = self.operator)
    except Exception as e:
      self.restoreCursor()
      return self.error_popup("Result import", e)
    if not outputMesh:
      self.restoreCursor()
      return self.error_popup("Not found", "MED result file not found.")
    #file naming is now done in the importMedToSmesh function so we can simplify our code

#    outputMesh.Compute() #no algorithms message for "Mesh_x" has been computed with warnings: -  global 1D algorithm is missing

    if salome.sg.hasDesktop():
      salome.sg.updateObjBrowser()
      self.restoreCursor()
      QMessageBox.about(self, "Compute","Computation successfully finished")
    else:
      print("Computation successfully finished")

    return True

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

    mySObject, myEntry = guihelper.getSObjectSelected()
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

__dialog=None

def getDialog():
  """
  This function returns a singleton instance of the plugin dialog.
  It is mandatory in order to call show without a parent ...
  """
  global __dialog
  if __dialog is None:
    __dialog = MeshBooleanDialog()
  return __dialog
