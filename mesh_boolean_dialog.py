# -*- coding: utf-8 -*-
# Copyright (C) 2007-2023  EDF
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

# Modules Python
# Modules Eficas

import os, subprocess
import tempfile
import re
import sys
import meshio
from MeshBooleanPlugin.MyPlugDialog_ui import Ui_MyPlugDialog
from MeshBooleanPlugin.myViewText import MyViewText
from qtsalome import *
from MeshBooleanPlugin.compute_values import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import qwt
from VTK.exec_VTK import VTK_main

verbose = True

OPERATOR_DICT = { 'Union' : 0, 'Intersection' : 1, 'Difference' : 2 }
ENGINE_DICT = { 'CGAL' : 0, 'igl' : 1, 'VTK' : 2, \
        'Interactive And Robust Mesh Booleans' : 3, 'Cork' : 4, 'mcut' : 5}
METRICS_DICT = { 'Execution Time' : 0, 'Average Quality' : 1 }

ENGINE_BENCHMARK_DICT = {\
        'CGAL is  is a C++ library that aims to provide easy access to efficient and reliable algorithms in computational geometry. It is known to provide robust algorithms.' : 0,\
        'igl is a C++ geometry processing library.' : 1,\
        """VTK is a software for 3D visualization and can be used to perform Boolean operations.
Our benchmark reveals that VTK is particularly slow, and this computational cost doesn't come with  a quality superior to the other engines.""" : 2,\
        'Interactive and Robust Mesh Booleans is the fastest of these engines. It is also very robust. However, the output mesh might contains double elements or free elements.' : 3, \
        """Cork is designed to support Boolean operations between triangle meshes.
Note that the development of this tool has stopped in 2013, and there are a lot of known issues.""" : 4,\
        """mcut is a C++ code that performs Booleans on meshes 'at fine scale'. It actually works with libigl.
It is widely used in the animation industry and in universities.
This code is not robust and fails on most edge cases of out benchmark.""" : 5}

NB_TRIANGLES = [972, 1940, 6958, 27320, 110324, 441496, 1765412]
UNION_TIME_DATA = [[0.1458, 0.2223, 0.5972, 1.8644, 7.4354, 33.7484, 190.1539], # CGAL
                    [0.1666, 0.2293, 0.247, 0.6063, 1.8354, 6.8085, 33.9464], # igl
                    [0.4118, 0.6189, 1.5142, 3.673, 11.3241, 52.2387], # VTK
                    [0.0208, 0.0254, 0.0603, 0.1648, 0.5673, 2.027, 8.3993], # IRMB
                    [0.0123, 0.0175, 0.0426, 0.1453, 0.6951, 3.4952, 20.1791], # Cork
                    [0.0279, 0.0413, 0.1113, 0.3806, 1.5812, 7.6355, 31.6626]] # mcut

INTERSECTION_TIME_DATA = [[0.1449, 0.2258, 0.5775, 1.8496, 7.2567, 33.5945, 190.2884], # CGAL
                    [0.1679, 0.2297, 0.2484, 0.6054, 1.8241, 6.4457, 36.9528], # igl
                    [0.4118, 0.6183, 1.5209, 3.6708, 10.9282, 55.9625], # VTK
                    [0.0201, 0.0247, 0.0582, 0.1572, 0.5295, 1.9357, 10.5941], # IRMB
                    [0.0119, 0.0168, 0.0408, 0.1391, 0.6435, 3.4335, 20.2468], # Cork
                    [0.0284, 0.0415, 0.1099, 0.3869, 1.6174, 7.7535, 35.3653]] # mcut

DIFFERENCE_TIME_DATA = [[0.1456, 0.2274, 0.6068, 1.8707, 7.3269, 33.8812, 204.5565], # CGAL
                    [0.1664, 0.2340, 0.2481, 0.6075, 1.8530, 6.6530, 38.7202], # igl
                    [0.4129, 0.6228, 1.5269, 3.7990, 10.9499, 56.4498], # VTK
                    [0.0207, 0.0264, 0.0592, 0.1674, 0.5472, 2.5907, 11.4418], # IRMB
                    [0.0120, 0.0174, 0.0441, 0.1533, 0.6761, 3.5862, 21.3695], # Cork
                    [0.0206, 0.0328, 0.0907, 0.3942, 1.5381, 7.6089, 34.9195]] # mcut


UNION_AVG_QUALITY_DATA = [[0.6390, 0.6744, 0.7384, 0.8186, 0.8761, 0.9114, 0.9309],
                        [0.6315, 0.6734, 0.7331, 0.8154, 0.8742, 0.9103, 0.9303],
                        [0.6065, 0.6474, 0.7227, 0.8101, 0.8707, 0.9084],
                        [0.5958, 0.6503, 0.7237, 0.8077, 0.8698, 0.9086, 0.9278],
                        [0.6387, 0.6741, 0.7382, 0.8184, 0.8760, 0.9113, 0.9308],
                        [0.6357, 0.6714, 0.7360, 0.8174, 0.8753, 0.9108, 0.9306]]

INTERSECTION_AVG_QUALITY_DATA = [[0.5895, 0.6424, 0.6993, 0.7928, 0.8592, 0.9030, 0.9266],
                        [0.5838, 0.6395, 0.6910, 0.7871, 0.8562, 0.9013, 0.9258],
                        [0.5489, 0.5937, 0.6601, 0.7688, 0.8455, 0.8954],
                        [0.6261, 0.6769, 0.6831, 0.7874, 0.8550, 0.8996, 0.9356],
                        [0.5890, 0.6417, 0.6989, 0.7926, 0.8590, 0.9029, 0.9265],
                        [0.5799, 0.6374, 0.6954, 0.7913, 0.8581, 0.9023, 0.9263]]

DIFFERENCE_AVG_QUALITY_DATA = [[0.6344, 0.7006, 0.7648, 0.8376, 0.8886, 0.9192, 0.9350],
                        [0.6284, 0.6982, 0.7588, 0.8335, 0.8866, 0.9180, 0.9345],
                        [0.5983, 0.6605, 0.7347, 0.8207, 0.8793, 0.9142],
                        [0.5958, 0.6503, 0.7237, 0.7999, 0.8698, 0.9054, 0.9278],
                        [0.6341, 0.7003, 0.7646, 0.8375, 0.8885, 0.9191, 0.9350],
                        [0.6318, 0.6878, 0.7676, 0.8374, 0.8907, 0.9164, 0.9360]]

class MeshBooleanDialog(Ui_MyPlugDialog,QWidget):
  """
  """
  def __init__(self):
    QWidget.__init__(self)
    self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
    self.setupUi(self)
    self.connecterSignaux()
    self.commande=""
    self.num=1
    self.__selectedMesh_L=None
    self.__selectedMesh_R=None
    self.meshIn_L=""
    self.isFile_L=False
    self.meshIn_R=""
    self.isFile_R=False
    self.operator=""

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
    self.COB_Engine.setCurrentIndex(1) # Same for the benchmark label
    self.COB_Engine.setCurrentIndex(0)

    self.resize(800, 600)

    self.maFenetre = None

  def connecterSignaux(self) :
    self.PB_Cancel.clicked.connect(self.PBCancelPressed)
    self.PB_Help.clicked.connect(self.PBHelpPressed)
    self.PB_OK.clicked.connect(self.PBOKPressed)

    self.LE_MeshFile_L.returnPressed.connect(lambda : self.meshFileNameChanged("L"))
    self.LE_MeshSmesh_L.returnPressed.connect(lambda : self.meshSmeshNameChanged("L"))
    self.PB_MeshFile_L.clicked.connect(lambda _: self.PBMeshFilePressed("L"))
    self.PB_MeshSmesh_L.clicked.connect(lambda _: self.PBMeshSmeshPressed("L"))
    self.LE_MeshFile_R.returnPressed.connect(lambda : self.meshFileNameChanged("R"))
    self.LE_MeshSmesh_R.returnPressed.connect(lambda : self.meshSmeshNameChanged("R"))
    self.PB_MeshFile_R.clicked.connect(lambda _: self.PBMeshFilePressed("R"))
    self.PB_MeshSmesh_R.clicked.connect(lambda _: self.PBMeshSmeshPressed("R"))
    #FIXME Do the same for _R

    self.COB_Operator.currentIndexChanged.connect(self.DisplayOperatorLabel)
    self.COB_Engine.currentIndexChanged.connect(self.DisplayEngineLabel)
    self.COB_Metric.currentIndexChanged.connect(self.update_graph)

  def GenMedFromAny(self, fileIn):
    if fileIn.endswith('.med'):
      return
    from salome.smesh import smeshBuilder
    smesh = smeshBuilder.New()
    self.fichierIn=tempfile.mktemp(suffix=".med",prefix="ForMMG_")
    if os.path.exists(self.fichierIn):
      os.remove(self.fichierIn)

    ext = os.path.splitext(fileIn)[-1]
    if ext == '.mesh' or ext == '.meshb':
      TmpMesh = smesh.CreateMeshesFromGMF(fileIn)[0]
    elif ext == '.cgns':
      TmpMesh = smesh.CreateMeshesFromCGNS(fileIn)[0][0]
    elif ext == '.stl':
      TmpMesh = smesh.CreateMeshesFromSTL(fileIn)
    elif ext == '.unv':
      TmpMesh = smesh.CreateMeshesFromUNV(fileIn)
    TmpMesh.ExportMED(self.fichierIn, autoDimension=True)
    smesh.RemoveMesh(TmpMesh)
    """
    TmpMesh = meshio.read(fileIn)
    TmpMesh.write(self.fichierIn, 'med')
    """

  def GenObjFromMed(self, zone):
    """zone = L or R"""
    if zone == "L":
      m = None
      if self.__selectedMesh_L is not None: # Case left is mesh
        self.meshIn_L=tempfile.mktemp(suffix=".stl",prefix="ForBMC_")
        if os.path.exists(self.meshIn_L):
          os.remove(self.meshIn_L)
        self.__selectedMesh_L.ExportSTL(self.meshIn_L, self.meshIn_L)
        m = meshio.read(self.meshIn_L)
        self.meshIn_L = os.path.splitext(self.meshIn_L)[0] + ".obj"
        m.write(self.meshIn_L)
      else: # Case left is file
        m = meshio.read(self.meshIn_L)
        self.meshIn_L=tempfile.mktemp(suffix=".obj",prefix="ForBMC_")
        if os.path.exists(self.meshIn_L):
          os.remove(self.meshIn_L)
        m.write(self.meshIn_L)
    else:
      if self.__selectedMesh_R is not None: # Case right is mesh
        self.__selectedMesh_R.ExportSTL(self.meshIn_R, self.meshIn_R)
        self.meshIn_R=tempfile.mktemp(suffix=".stl",prefix="ForBMC_")
        if os.path.exists(self.meshIn_R):
          os.remove(self.meshIn_R)
        m = meshio.read(self.meshIn_R)
        m.write(os.path.splitext(self.meshIn_R)[0] + ".obj")
      else: # Case right is file
        m = meshio.read(self.meshIn_R)
        self.meshIn_R=tempfile.mktemp(suffix=".stl",prefix="ForBMC_")
        if os.path.exists(self.meshIn_R):
          os.remove(self.meshIn_R)
        m.write(self.meshIn_R)
        m = meshio.read(self.meshIn_R) # Manip to avoid meshio from crashing if tetra cells
        self.meshIn_R = os.path.splitext(self.meshIn_R)[0] + ".obj"
        m.write(self.meshIn_R)

  def update_graph(self):
    from PyQt5 import QtCore
    _translate = QtCore.QCoreApplication.translate
    data = []
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
    curve.setData(NB_TRIANGLES, data[self.COB_Engine.currentIndex()],\
            len(data[self.COB_Engine.currentIndex()]))
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
    engine = ''
    for key, val in ENGINE_DICT.items():
      if val == self.COB_Engine.currentIndex():
        engine = key
    self.label_Graph_Title.setText(_translate("MyPlugDialog", f"<-\nPerformences of {engine} on the {self.operator.lower()} operator, measuring the {metric.lower()}."))

    self.QP_Benchmark.replot()


  def DisplayOperatorLabel(self):
    from PyQt5 import QtCore, QtGui, QtWidgets
    _translate = QtCore.QCoreApplication.translate
    for key, val in OPERATOR_DICT.items():
      if self.COB_Operator.currentIndex() == val:
        self.label_Operator.setText(_translate("MyPlugDialog", f"Compute the {key.lower()} of the two meshes selected."))
    self.update_graph()

  def DisplayEngineLabel(self):
    from PyQt5 import QtCore, QtGui, QtWidgets
    _translate = QtCore.QCoreApplication.translate
    for key, val in ENGINE_DICT.items():
      if self.COB_Engine.currentIndex() == val:
        self.label_Engine.setText(_translate("MyPlugDialog", f"Compute with the {key} engine"))
    for key, val in ENGINE_BENCHMARK_DICT.items():
      if self.COB_Engine.currentIndex() == val:
        self.label_Benchmark.setText(_translate("MyPlugDialog", key))
    self.update_graph()

  def PBHelpPressed(self):
    QMessageBox.about(None, "About this MMG remeshing tool",
            """
                    Adapt your mesh with MMG
                    -------------------------------------------

This tool allows your to adapt your mesh after a
Boolean operation. It also allows you to repair a
bad mesh (double elements or free elements).

By default, your mesh will be prepared for MMG.
You can find the options to disable it or
explicitely generate the repaired mesh in the
'Advanced Remeshing Options' panel.
By pressing the 'Remesh' button, your mesh will
be adapted by MMG with your selected parameters.
You can change the parameters to better fit you
needs than with the default ones. Restore the
default parameters by clicking on the 'Compute
Default Values' button.
            """)

  def prepareFichier(self, zone):
    """zone = L or R"""
    self.GenObjFromMed(zone)

  def PBOKPressed(self):
    import salome
    import SMESH
    from salome.kernel import studyedit
    from salome.smesh import smeshBuilder
    if self.meshIn_R=="" or self.meshIn_R=="":
      QMessageBox.critical(self, "Mesh", "select an input mesh")
      return False
    if self.__selectedMesh_L is not None or not self.meshIn_L.endswith(".obj"): self.prepareFichier("L")
    if self.__selectedMesh_R is not None or not self.meshIn_R.endswith(".obj"): self.prepareFichier("R")
    if not (os.path.isfile(self.meshIn_L)):
      QMessageBox.critical(self, "File", "unable to read GMF Mesh in "+str(self.meshIn_L))
      return False
    if not (os.path.isfile(self.meshIn_R)):
      QMessageBox.critical(self, "File", "unable to read GMF Mesh in "+str(self.meshIn_R))
      return False


    print(self.meshIn_L, self.meshIn_R)

    result_file =tempfile.mktemp(suffix=".med",prefix="ForBMC_")
    if os.path.exists(result_file):
      os.remove(result_file)
    if (self.COB_Engine.currentIndex() == ENGINE_DICT['VTK']):
      VTK_main(self.operator.lower(), self.meshIn_L, self.meshIn_R, result_file)

    smesh = smeshBuilder.New()
    maStudy=salome.myStudy
    smesh.UpdateStudy()
    (outputMesh, status) = smesh.CreateMeshesFromMED(result_file)
    outputMesh=outputMesh[0]
    name = self.operator + '_' + str(self.num)
    smesh.SetName(outputMesh.GetMesh(), name)
    outputMesh.Compute() #no algorithms message for "Mesh_x" has been computed with warnings: -  global 1D algorithm is missing

    if salome.sg.hasDesktop(): salome.sg.updateObjBrowser()
    self.num+=1
    return True

  def getResumeData(self, separator="\n"):
    text=""
    text+="RepairBeforeCompute="+str(self.CB_RepairBeforeCompute.isChecked())+separator
    text+="SwapEdge="+str(self.CB_SwapEdge.isChecked())+separator
    text+="MoveEdge="+str(self.CB_MoveEdge.isChecked())+separator
    text+="InsertEdge="+str(self.CB_InsertEdge.isChecked())+separator
    text+="GeometricalApproximation="+str(self.SP_Geomapp.value())+separator
    text+="Hmin="+str(self.SP_Hmin.value())+separator
    text+="Hmax="+str(self.SP_Hmax.value())+separator
    text+="MeshGradation="+str(self.SP_Gradation.value())+separator
    return str(text)

  def PBCancelPressed(self):
    self.close()

  def PBMeshFilePressed(self, zone):
    """zone = L or R"""
    filter_string = "All mesh formats (*.unv *.cgns *.mesh *.meshb *.med *.stl)"

    if zone == 'L':
      fd = QFileDialog(self, "select an existing mesh file", self.LE_MeshFile_L.text(), filter_string + ";;All Files (*)")
    else :
      fd = QFileDialog(self, "select an existing mesh file", self.LE_MeshFile_R.text(), filter_string + ";;All Files (*)")
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

  def PBMeshSmeshPressed(self, zone):
    """zone = L or R"""
    from omniORB import CORBA
    import salome
    from salome.kernel import studyedit
    from salome.smesh.smeshstudytools import SMeshStudyTools
    from salome.gui import helper as guihelper
    from salome.smesh import smeshBuilder
    smesh = smeshBuilder.New()

    mySObject, myEntry = guihelper.getSObjectSelected()
    if CORBA.is_nil(mySObject) or mySObject==None:
      QMessageBox.critical(self, "Mesh", "select an input mesh")
      return
    self.smeshStudyTool = SMeshStudyTools()
    try:
      if zone == "L":
          self.__selectedMesh_L = self.smeshStudyTool.getMeshObjectFromSObject(mySObject)
      else:
          self.__selectedMesh_R = self.smeshStudyTool.getMeshObjectFromSObject(mySObject)
    except:
      QMessageBox.critical(self, "Mesh", "select an input mesh")
      return
    if zone == "L":
      if CORBA.is_nil(self.__selectedMesh_L):
        QMessageBox.critical(self, "Mesh", "select an input mesh")
        return
    else:
      if CORBA.is_nil(self.__selectedMesh_L):
        QMessageBox.critical(self, "Mesh", "select an input mesh")
        return
    myName = mySObject.GetName()

    if zone == 'L':
      #self.currentName = myName
      self.meshIn_L=myName
      self.LE_MeshSmesh_L.setText(myName)
      self.LE_MeshFile_L.setText("")
      self.isFile_L = False
    else:
      #self.currentName = myName
      self.meshIn_R=myName
      self.LE_MeshSmesh_R.setText(myName)
      self.LE_MeshFile_R.setText("")
      self.isFile_R = False

  def meshFileNameChanged(self, zone):
    """zone = L or R"""
    #FIXME Change in name Gen new med
    if zone == 'L':
      self.meshIn_L=str(self.LE_MeshFile_L.text())
      self.isFile_L=False
      if os.path.exists(self.meshIn_L): 
        self.__selectedMesh_L=None
        self.LE_MeshSmesh_L.setText("")
        #self.currentname = os.path.basename(self.fichierIn)
        return
    else:
      self.meshIn_R=str(self.LE_MeshFile_R.text())
      self.isFile_R=False
      if os.path.exists(self.meshIn_R): 
        self.__selectedMesh_R=None
        self.LE_MeshSmesh_R.setText("")
        #self.currentname = os.path.basename(self.fichierIn)
        return
    QMessageBox.warning(self, "Mesh file", "File doesn't exist")

  def meshSmeshNameChanged(self, zone):
    """only change by GUI mouse selection, otherwise clear // zone = L or R"""
    if zone == 'L':
      self.__selectedMesh_L = None
      self.LE_MeshSmesh_L.setText("")
      self.meshIn_L = ""
    else:
      self.__selectedMesh_R = None
      self.LE_MeshSmesh_R.setText("")
      self.meshIn_R = ""
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
