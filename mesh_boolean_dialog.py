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
from meshbooleanplugin.MyPlugDialog_ui import Ui_MyPlugDialog
from qtsalome import *
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import QMessageBox
import qwt

from meshbooleanplugin.vtk import exec_vtk
from meshbooleanplugin.irmb import exec_irmb
from meshbooleanplugin.cork import exec_cork
from meshbooleanplugin.mcut import exec_mcut
from meshbooleanplugin.libigl import exec_libigl
from meshbooleanplugin.cgal import exec_cgal

from meshbooleanplugin.mesh_boolean_utils import meshIOConvert
import platform
from enum import Enum

from salome.smesh import smeshBuilder
smesh = smeshBuilder.New()

import SalomePyQt
sgPyQt=SalomePyQt.SalomePyQt()

translate=QCoreApplication.translate

#To show messages of error without modifying the script
debug_plugin = os.getenv("DEBUG_PLUGIN")
if debug_plugin or verbose():
  positionVerbosityOfLogger(logging.DEBUG)

class BooleanMeshAlgorithm(str, Enum):
  CGAL = 'CGAL'
  IGL  = 'igl'
  VTK  = 'vtk'
  IRMB = 'irmb'
  CORK = 'cork'
  MCUT = 'mcut'

OPERATOR_DICT = { 'Union' : 0, 'Intersection' : 1, 'Difference' : 2 }
METRICS_DICT = { 'Execution Time' : 0, 'Average Quality' : 1 }

ENGINE_BENCHMARK_DICT={BooleanMeshAlgorithm.CGAL : """CGAL is  is a C++ library that aims to provide easy access to efficient and reliable algorithms in computational geometry.
It is known to provide robust algorithms.""",
                       BooleanMeshAlgorithm.IGL  : """IGL is a C++ geometry processing library.""",
                       BooleanMeshAlgorithm.VTK  : """VTK is a software for 3D visualization and can be used to perform Boolean operations.
Our benchmark reveals that VTK is particularly slow, and this computational cost doesn't come with  a quality superior to the other engines.""",
                       BooleanMeshAlgorithm.IRMB : """IRMB Interactive and Robust Mesh Booleans is the fastest of these engines. It is also very robust.
However, the output mesh might contains double elements or free elements.
In addition, this code can fail to understand the orientation of a mesh, which leads to an inverted inside/out determination.""",
                       BooleanMeshAlgorithm.CORK : """Cork is designed to support Boolean operations between triangle meshes.
Note that the development of this tool has stopped in 2013, and there are a lot of known issues.""",
                       BooleanMeshAlgorithm.MCUT : """MCut is a C++ code that performs Booleans on meshes 'at fine scale'. It actually works with libigl.
It is widely used in the animation industry and in universities.
This code is not robust and fails on most edge cases of out benchmark."""
                       }

LICENSE_DICT = { BooleanMeshAlgorithm.CGAL : 'GPL and LGPL',
                 BooleanMeshAlgorithm.IGL  : 'MPL2',
                 BooleanMeshAlgorithm.VTK  : 'BSD-3',
                 BooleanMeshAlgorithm.IRMB : 'MIT',
                 BooleanMeshAlgorithm.CORK : 'LGPL',
                 BooleanMeshAlgorithm.MCUT : 'GPL and commercial'
                }

NB_TRIANGLES = [972, 1940, 6958, 27320, 110324, 441496, 1765412]
UNION_TIME_DATA = { BooleanMeshAlgorithm.CGAL : [0.1458, 0.2223, 0.5972, 1.8644, 7.4354, 33.7484, 190.1539],
                    BooleanMeshAlgorithm.IGL  : [0.1666, 0.2293, 0.247, 0.6063, 1.8354, 6.8085, 33.9464],
                    BooleanMeshAlgorithm.VTK  : [0.4118, 0.6189, 1.5142, 3.673, 11.3241, 52.2387],
                    BooleanMeshAlgorithm.IRMB : [0.0208, 0.0254, 0.0603, 0.1648, 0.5673, 2.027, 8.3993],
                    BooleanMeshAlgorithm.CORK : [0.0123, 0.0175, 0.0426, 0.1453, 0.6951, 3.4952, 20.1791],
                    BooleanMeshAlgorithm.MCUT : [0.0279, 0.0413, 0.1113, 0.3806, 1.5812, 7.6355, 31.6626]
                   }

INTERSECTION_TIME_DATA = { BooleanMeshAlgorithm.CGAL : [0.1449, 0.2258, 0.5775, 1.8496, 7.2567, 33.5945, 190.2884],
                           BooleanMeshAlgorithm.IGL  : [0.1679, 0.2297, 0.2484, 0.6054, 1.8241, 6.4457, 36.9528],
                           BooleanMeshAlgorithm.VTK  : [0.4118, 0.6183, 1.5209, 3.6708, 10.9282, 55.9625],
                           BooleanMeshAlgorithm.IRMB : [0.0201, 0.0247, 0.0582, 0.1572, 0.5295, 1.9357, 10.5941],
                           BooleanMeshAlgorithm.CORK : [0.0119, 0.0168, 0.0408, 0.1391, 0.6435, 3.4335, 20.2468],
                           BooleanMeshAlgorithm.MCUT  : [0.0284, 0.0415, 0.1099, 0.3869, 1.6174, 7.7535, 35.3653]
                          }

DIFFERENCE_TIME_DATA = { BooleanMeshAlgorithm.CGAL : [0.1456, 0.2274, 0.6068, 1.8707, 7.3269, 33.8812, 204.5565],
                         BooleanMeshAlgorithm.IGL  : [0.1664, 0.2340, 0.2481, 0.6075, 1.8530, 6.6530, 38.7202],
                         BooleanMeshAlgorithm.VTK  : [0.4129, 0.6228, 1.5269, 3.7990, 10.9499, 56.4498],
                         BooleanMeshAlgorithm.IRMB : [0.0207, 0.0264, 0.0592, 0.1674, 0.5472, 2.5907, 11.4418],
                         BooleanMeshAlgorithm.CORK : [0.0120, 0.0174, 0.0441, 0.1533, 0.6761, 3.5862, 21.3695],
                         BooleanMeshAlgorithm.MCUT : [0.0206, 0.0328, 0.0907, 0.3942, 1.5381, 7.6089, 34.9195]
                        }


UNION_AVG_QUALITY_DATA = { BooleanMeshAlgorithm.CGAL : [0.6390, 0.6744, 0.7384, 0.8186, 0.8761, 0.9114, 0.9309],
                           BooleanMeshAlgorithm.IGL  : [0.6315, 0.6734, 0.7331, 0.8154, 0.8742, 0.9103, 0.9303],
                           BooleanMeshAlgorithm.VTK  : [0.6065, 0.6474, 0.7227, 0.8101, 0.8707, 0.9084],
                           BooleanMeshAlgorithm.IRMB : [0.5958, 0.6503, 0.7237, 0.8077, 0.8698, 0.9086, 0.9278],
                           BooleanMeshAlgorithm.CORK : [0.6387, 0.6741, 0.7382, 0.8184, 0.8760, 0.9113, 0.9308],
                           BooleanMeshAlgorithm.MCUT : [0.6357, 0.6714, 0.7360, 0.8174, 0.8753, 0.9108, 0.9306]
                          }

INTERSECTION_AVG_QUALITY_DATA = { BooleanMeshAlgorithm.CGAL : [0.5895, 0.6424, 0.6993, 0.7928, 0.8592, 0.9030, 0.9266],
                                  BooleanMeshAlgorithm.IGL  : [0.5838, 0.6395, 0.6910, 0.7871, 0.8562, 0.9013, 0.9258],
                                  BooleanMeshAlgorithm.VTK  : [0.5489, 0.5937, 0.6601, 0.7688, 0.8455, 0.8954],
                                  BooleanMeshAlgorithm.IRMB : [0.6261, 0.6769, 0.6831, 0.7874, 0.8550, 0.8996, 0.9356],
                                  BooleanMeshAlgorithm.CORK : [0.5890, 0.6417, 0.6989, 0.7926, 0.8590, 0.9029, 0.9265],
                                  BooleanMeshAlgorithm.MCUT : [0.5799, 0.6374, 0.6954, 0.7913, 0.8581, 0.9023, 0.9263]
                                 }

DIFFERENCE_AVG_QUALITY_DATA = { BooleanMeshAlgorithm.CGAL : [0.6344, 0.7006, 0.7648, 0.8376, 0.8886, 0.9192, 0.9350],
                                BooleanMeshAlgorithm.IGL  : [0.6284, 0.6982, 0.7588, 0.8335, 0.8866, 0.9180, 0.9345],
                                BooleanMeshAlgorithm.VTK  : [0.5983, 0.6605, 0.7347, 0.8207, 0.8793, 0.9142],
                                BooleanMeshAlgorithm.IRMB : [0.5958, 0.6503, 0.7237, 0.7999, 0.8698, 0.9054, 0.9278],
                                BooleanMeshAlgorithm.CORK : [0.6341, 0.7003, 0.7646, 0.8375, 0.8885, 0.9191, 0.9350],
                                BooleanMeshAlgorithm.MCUT : [0.6318, 0.6878, 0.7676, 0.8374, 0.8907, 0.9164, 0.9360]
                               }

def getTmpFileName(suffix=None, prefix=None):
  tempdir = tempfile.gettempdir()
  tmp_file = tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, dir=tempdir, delete=False)
  tmp_filename = tmp_file.name
  return tmp_filename


def runAlgo(algo, operator, mesh_left, mesh_right, result_file):
  logger.debug("in runAlgo")
  if algo == BooleanMeshAlgorithm.VTK :
    p = exec_vtk.VTK_main(operator, mesh_left, mesh_right, result_file)
  elif algo == BooleanMeshAlgorithm.IRMB :
    p = exec_irmb.IRMB_main(operator, mesh_left, mesh_right, result_file)
  elif algo == BooleanMeshAlgorithm.CORK :
    p = exec_cork.cork_main(operator, mesh_left, mesh_right, result_file)
  elif algo == BooleanMeshAlgorithm.MCUT :
    p = exec_mcut.mcut_main(operator, mesh_left, mesh_right, result_file)
  elif algo == BooleanMeshAlgorithm.IGL :
    p = exec_libigl.libigl_main(operator, mesh_left, mesh_right, result_file)
  elif algo == BooleanMeshAlgorithm.CGAL :
    p = exec_cgal.cgal_main(operator, mesh_left, mesh_right, result_file)
  else:
    raise ValueError("Unknown algorithm!")
  return p

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
    from PyQt5 import QtCore
    QWidget.__init__(self)
    self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
    self.worker = None
    self.setupUi(self)
    self.connecterSignaux()
    self.commande=""
    self.union_num=1
    self.intersection_num=1
    self.difference_num=1
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

    self.COB_Operator.setCurrentIndex(1) # Needed to trigger the graph update
    self.COB_Operator.setCurrentIndex(0) # Needed to trigger the graph update
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
    self.COB_Metric.currentIndexChanged.connect(self.updateGraph)

  def displaySummupLabel(self):
    from PyQt5 import QtCore
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

  def updateGraph(self):
    from PyQt5 import QtCore
    _translate = QtCore.QCoreApplication.translate
    data = {}
    if self.COB_Metric.currentIndex() == METRICS_DICT['Execution Time']:
      data = DIFFERENCE_TIME_DATA
      if self.COB_Operator.currentIndex() == OPERATOR_DICT['Union']:
        data = UNION_TIME_DATA
      elif self.COB_Operator.currentIndex() == OPERATOR_DICT['Intersection']:
        data = INTERSECTION_TIME_DATA
    elif self.COB_Metric.currentIndex() == METRICS_DICT['Average Quality']:
      data = DIFFERENCE_AVG_QUALITY_DATA
      if self.COB_Operator.currentIndex() == OPERATOR_DICT['Union']:
        data = UNION_AVG_QUALITY_DATA
      elif self.COB_Operator.currentIndex() == OPERATOR_DICT['Intersection']:
        data = INTERSECTION_AVG_QUALITY_DATA

    curve = qwt.QwtPlotCurve("Benchmark curve")
    curve.setData(NB_TRIANGLES, data[self.getCurrentAlgorithm()], len(data[self.getCurrentAlgorithm()]))
    self.QP_Benchmark.detachItems()
    curve.attach(self.QP_Benchmark)
    self.QP_Benchmark.setAxisAutoScale(True)
    self.QP_Benchmark.setAxisTitle(qwt.QwtPlot.xBottom, "Number of triangles")
    metric = ""
    for key, val in METRICS_DICT.items():
      if val == self.COB_Metric.currentIndex():
        metric = key
    self.QP_Benchmark.setAxisTitle(qwt.QwtPlot.yLeft, metric)
    self.operator = ''
    for key, val in OPERATOR_DICT.items():
      if val == self.COB_Operator.currentIndex():
        self.operator = key
    engine = self.getCurrentAlgorithm().value
    self.label_Graph_Title.setText(_translate("MyPlugDialog", f"<-\nPerformences of {engine} on the {self.operator.lower()} operator, measuring the {metric.lower()}."))

    self.QP_Benchmark.replot()
    self.displaySummupLabel()

  def displayOperatorLabel(self):
    from PyQt5 import QtCore, QtGui, QtWidgets
    _translate = QtCore.QCoreApplication.translate
    for key, val in OPERATOR_DICT.items():
      if self.COB_Operator.currentIndex() == val:
        self.label_Operator.setText(_translate("MyPlugDialog", f"Compute the {key.lower()} of the two meshes selected."))
    self.updateGraph()

  def displayEngineLabel(self):
    from PyQt5 import QtCore, QtGui, QtWidgets
    _translate = QtCore.QCoreApplication.translate
    self.label_Engine.setText(_translate("MyPlugDialog", f"This engine is used under the {LICENSE_DICT[self.getCurrentAlgorithm()]} license."))
    self.label_Benchmark.setText(_translate("MyPlugDialog", ENGINE_BENCHMARK_DICT[self.getCurrentAlgorithm()]))
    self.updateGraph()

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
    if not (os.path.isfile(self.meshIn_L)):
      self.restoreCursor()
      return self.error_popup("File", "unable to read mesh in "+str(self.meshIn_L))
    if not (os.path.isfile(self.meshIn_R)):
      self.restoreCursor()
      return self.error_popup("File", "unable to read mesh in "+str(self.meshIn_R))

    self.result_file = getTmpFileName(suffix=".med",prefix="ForBMC_")

    self.thread = QThread()
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

    logger.debug(f"return code: {self.worker.returncode}")
    if (self.worker.returncode) != 0:
      self.restoreCursor()
      self.error_popup("Error", "Computation ended in error.")
      return

    #see which algorithm is called to convert the appropriate result into a .med file
    algo = self.getCurrentAlgorithm()
    if algo == BooleanMeshAlgorithm.CGAL:
      exec_cgal.convert_result(self.result_file)
    elif algo == BooleanMeshAlgorithm.MCUT:
      exec_mcut.convert_result(self.result_file)
    elif algo == BooleanMeshAlgorithm.CORK:
      exec_cork.convert_result(self.result_file)
    elif algo == BooleanMeshAlgorithm.IRMB:
      exec_irmb.convert_result(self.result_file)
    elif algo == BooleanMeshAlgorithm.IGL:
      exec_libigl.convert_result(self.result_file)
    elif algo == BooleanMeshAlgorithm.VTK:
      exec_vtk.convert_result(self.result_file)

    smesh.UpdateStudy()

    try:
      (outputMesh, status) = smesh.CreateMeshesFromMED(self.result_file)
    except Exception as e:
      self.restoreCursor()
      return self.error_popup("Result import", e)
    if len(outputMesh) == 0:
      self.restoreCursor()
      return self.error_popup("Not found", "MED result file not found.")
    outputMesh=outputMesh[0]
    name = ""
    if self.operator.lower() == 'union':
      name = self.operator + '_' + str(self.union_num)
      self.union_num+=1
    elif self.operator.lower() == 'intersection':
      name = self.operator + '_' + str(self.intersection_num)
      self.intersection_num+=1
    else:
      name = self.operator + '_' + str(self.difference_num)
      self.difference_num+=1
    smesh.SetName(outputMesh.GetMesh(), name)
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
    if CORBA.is_nil(mySObject) or mySObject==None:
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
