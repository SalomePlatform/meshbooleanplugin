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
from MeshBooleanPlugin.MyPlugDialog_ui import Ui_MyPlugDialog
from MeshBooleanPlugin.myViewText import MyViewText
from qtsalome import *
from MeshBooleanPlugin.compute_values import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

verbose = True

OPERATOR_DICT = { 'Union' : 0, 'Intersection' : 1, 'Difference' : 3 }
ENGINE_DICT = { 'CGAL' : 0, 'igl' : 1, 'VTK' : 2, \
        'Interactive And Robust Mesh Booleans' : 3, 'Cork' : 4, 'mcut' : 5}

class MeshBooleanDialog(Ui_MyPlugDialog,QWidget):
  """
  """
  def __init__(self):
    QWidget.__init__(self)
    self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
    self.setupUi(self)
    self.connecterSignaux()
    self.fichierIn=""
    self.fichierOut=""
    self.MeshIn=""
    self.commande=""
    self.num=1
    self.numRepair=1
    self.__selectedMesh=None
    self.values = None
    self.isFile = False
    self.currentName = ""

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
    #self.clean()
    self.NbOptParam = 0

    self.maFenetre = None

  def connecterSignaux(self) :
    self.PB_Cancel.clicked.connect(self.PBCancelPressed)
    self.PB_Default.clicked.connect(self.clean)
    self.PB_Help.clicked.connect(self.PBHelpPressed)
    self.PB_OK.clicked.connect(self.PBOKPressed)

    self.LE_MeshFile_L.returnPressed.connect(self.meshFileNameChanged)
    self.LE_MeshSmesh_L.returnPressed.connect(self.meshSmeshNameChanged)
    self.PB_MeshFile_L.clicked.connect(self.PBMeshFilePressed)
    self.PB_MeshSmesh_L.clicked.connect(self.PBMeshSmeshPressed)
    #FIXME Do the same for _R

    self.COB_Operator.currentIndexChanged.connect(self.DisplayOperatorLabel)
    self.COB_Engine.currentIndexChanged.connect(self.DisplayEngineLabel)

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

  def GenMeshFromMed(self):
    create_mesh = False
    if self.__selectedMesh is None:
      from salome.smesh import smeshBuilder
      smesh = smeshBuilder.New()
      self.__selectedMesh = smesh.CreateMeshesFromMED(self.fichierIn)[0][0]
      create_mesh = True
    self.fichierIn=tempfile.mktemp(suffix=".mesh",prefix="ForMMG_")
    if os.path.exists(self.fichierIn):
      os.remove(self.fichierIn)

    if self.__selectedMesh is not None:
      if str(type(self.__selectedMesh)) == "<class 'salome.smesh.smeshBuilder.Mesh'>":
        self.__selectedMesh.ExportGMF(self.fichierIn)
      else:
        self.__selectedMesh.ExportGMF(self.__selectedMesh, self.fichierIn, True)
    else:
      QMessageBox.critical(self, "Mesh", "internal error")
    if create_mesh:
        smesh.RemoveMesh(self.__selectedMesh)

  def DisplayOperatorLabel(self):
    from PyQt5 import QtCore, QtGui, QtWidgets
    _translate = QtCore.QCoreApplication.translate
    if self.COB_Operator.currentIndex() == OPERATOR_DICT['Union']:
      self.label_Operator.setText(_translate("MyPlugDialog", "Compute the union of the two meshes selected."))
    elif self.COB_Operator.currentIndex() == OPERATOR_DICT['Intersection']:
      self.label_Operator.setText(_translate("MyPlugDialog", "Compute the intersection of the two meshes selected."))
    else:
      self.label_Operator.setText(_translate("MyPlugDialog", "Compute the difference of the two meshes selected"))

  def DisplayEngineLabel(self):
    from PyQt5 import QtCore, QtGui, QtWidgets
    _translate = QtCore.QCoreApplication.translate
    print(self.COB_Engine.currentIndex())
    if self.COB_Engine.currentIndex() == ENGINE_DICT['CGAL']:
      self.label_Engine.setText(_translate("MyPlugDialog", "Compute with CGAL engine"))
    elif self.COB_Engine.currentIndex() == ENGINE_DICT['igl']:
      self.label_Engine.setText(_translate("MyPlugDialog", "Compute with igl engine"))
    elif self.COB_Engine.currentIndex() == ENGINE_DICT['VTK']:
      self.label_Engine.setText(_translate("MyPlugDialog", "Compute with VTK engine"))
    elif self.COB_Engine.currentIndex() == ENGINE_DICT['Interactive And Robust Mesh Booleans']:
      self.label_Engine.setText(_translate("MyPlugDialog", "Compute with Interactive And Robust Mesh Booleans engine"))
    elif self.COB_Engine.currentIndex() == ENGINE_DICT['Cork']:
      self.label_Engine.setText(_translate("MyPlugDialog", "Compute with Cork engine"))
    else:
      self.label_Engine.setText(_translate("MyPlugDialog", "Compute with mcut engine"))

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

  def PBOKPressed(self):
    if self.fichierIn=="" and self.MeshIn=="":
      QMessageBox.critical(self, "Mesh", "select an input mesh")
      return False

    ext = os.path.splitext(self.fichierIn)[-1]
    if self.isFile and ext != '.med' \
        and self.COB_Remesher.currentIndex() == REMESHER_DICT['MMGS']:
      if not ((ext == 'mesh' or ext == '.meshb') and not (self.CB_RepairBeforeCompute.isChecked() or self.CB_RepairOnly.isChecked())):
          self.GenMedFromAny(self.fichierIn)

    CpyFichierIn = self.fichierIn
    CpyMeshIn = self.MeshIn
    CpySelectedMesh = self.__selectedMesh
    if (self.CB_RepairBeforeCompute.isChecked() or self.CB_RepairOnly.isChecked()) and self.COB_Remesher.currentIndex() == REMESHER_DICT['MMGS']:
      if self.values is None:
        if self.fichierIn != "":
          self.values = Values(self.fichierIn, 0, self.currentName)
        else:
          self.values = Values(self.MeshIn, 0, self.currentName)
      self.Repair()
      if not self.CB_GenRepair.isChecked() and not self.CB_RepairOnly.isChecked():
        self.numRepair-=1
    if not self.CB_RepairOnly.isChecked():
      ext = os.path.splitext(self.fichierIn)[-1]
      if self.fichierIn != "":
        if ext == '.med':
          self.GenMeshFromMed()
        elif ext != '.mesh' and ext != '.meshb':
          self.GenMedFromAny(self.fichierIn)
          self.GenMeshFromMed()
        self.__selectedMesh = None

      if not(self.PrepareLigneCommande()):
        #warning done yet
        #QMessageBox.warning(self, "Compute", "Command not found")
        return False

      self.maFenetre=MyViewText(self,self.commande)
      if (not self.CB_GenRepair.isChecked()) and self.values is not None:
        self.values.DeleteMesh()

    self.fichierIn = CpyFichierIn
    self.MeshIn = CpyMeshIn
    self.__selectedMesh = CpySelectedMesh
    self.values = None
    return True

  def enregistreResultat(self):
    import salome
    import SMESH
    from salome.kernel import studyedit
    from salome.smesh import smeshBuilder
    smesh = smeshBuilder.New()

    if not os.path.isfile(self.fichierOut):
      QMessageBox.warning(self, "Compute", "Result file "+self.fichierOut+" not found")

    maStudy=salome.myStudy
    smesh.UpdateStudy()
    self.GenMedFromAny(self.fichierOut)
    (outputMesh, status) = smesh.CreateMeshesFromMED(self.fichierIn)
    outputMesh=outputMesh[0]
    name=str(self.LE_MeshSmesh.text())
    initialMeshFile=None
    initialMeshObject=None
    if name=="":
      if self.MeshIn =="":
        a = re.sub(r'_\d*$', '', str(self.fichierIn))
      else: # Repaired
        a = re.sub(r'_\d*$', '', str(self.MeshIn))
      name=os.path.basename(os.path.splitext(a)[0])
      initialMeshFile=a

    else:
      initialMeshObject=maStudy.FindObjectByName(name ,"SMESH")[0]

    meshname = self.currentName+"_MMG_"+str(self.num)
    smesh.SetName(outputMesh.GetMesh(), meshname)
    outputMesh.Compute() #no algorithms message for "Mesh_x" has been computed with warnings: -  global 1D algorithm is missing

    self.editor = studyedit.getStudyEditor()
    moduleEntry=self.editor.findOrCreateComponent("SMESH","SMESH")
    HypReMeshEntry = self.editor.findOrCreateItem(
        moduleEntry, name = "Plugins Hypotheses", icon="mesh_tree_hypo.png") #, comment = "HypoForRemeshing" )

    monStudyBuilder=maStudy.NewBuilder()
    monStudyBuilder.NewCommand()
    newStudyIter=monStudyBuilder.NewObject(HypReMeshEntry)
    self.editor.setAttributeValue(newStudyIter, "AttributeName", "MMG Parameters_"+str(self.num))
    self.editor.setAttributeValue(newStudyIter, "AttributeComment", self.getResumeData(separator=" ; "))
    
    SOMesh=maStudy.FindObjectByName(meshname ,"SMESH")[0]
    
    if initialMeshFile!=None:
      newStudyFileName=monStudyBuilder.NewObject(SOMesh)
      self.editor.setAttributeValue(newStudyFileName, "AttributeName", "meshFile")
      self.editor.setAttributeValue(newStudyFileName, "AttributeExternalFileDef", initialMeshFile)
      self.editor.setAttributeValue(newStudyFileName, "AttributeComment", initialMeshFile)

    if initialMeshObject!=None:
      newLink=monStudyBuilder.NewObject(SOMesh)
      monStudyBuilder.Addreference(newLink, initialMeshObject)

    newLink=monStudyBuilder.NewObject(SOMesh)
    monStudyBuilder.Addreference(newLink, newStudyIter)

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

  def PBMeshFilePressed(self):
    filter_string = "All mesh formats (*.unv *.cgns *.mesh *.meshb *.med *.stl)"

    fd = QFileDialog(self, "select an existing mesh file", self.LE_MeshFile_L.text(), filter_string + ";;All Files (*)")
    if fd.exec_():
      infile = fd.selectedFiles()[0]
      self.LE_MeshFile_L.setText(infile)
      self.fichierIn=str(infile)
      self.currentName = os.path.splitext(os.path.basename(self.fichierIn))[0]
      self.MeshIn=""
      self.LE_MeshSmesh_L.setText("")
      self.__selectedMesh=None
      self.isFile = True

  def PBMeshSmeshPressed(self):
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
      self.__selectedMesh = self.smeshStudyTool.getMeshObjectFromSObject(mySObject)
    except:
      QMessageBox.critical(self, "Mesh", "select an input mesh")
      return
    if CORBA.is_nil(self.__selectedMesh):
      QMessageBox.critical(self, "Mesh", "select an input mesh")
      return
    myName = mySObject.GetName()

    self.MeshIn=myName
    self.currentName = myName
    self.LE_MeshSmesh_L.setText(myName)
    self.LE_MeshFile_L.setText("")
    self.fichierIn=""
    self.isFile = False

  def meshFileNameChanged(self):
    #FIXME Change in name Gen new med
    self.fichierIn=str(self.LE_MeshFile_L.text())
    if os.path.exists(self.fichierIn): 
      self.__selectedMesh=None
      self.MeshIn=""
      self.LE_MeshSmesh_L.setText("")
      self.currentname = os.path.basename(self.fichierIn)
      return
    QMessageBox.warning(self, "Mesh file", "File doesn't exist")

  def meshSmeshNameChanged(self):
    """only change by GUI mouse selection, otherwise clear"""
    self.__selectedMesh = None
    self.MeshIn=""
    self.LE_MeshSmesh_L.setText("")
    self.fichierIn=""
    return

  def prepareFichier(self):
    self.GenMeshFromMed()

  def PrepareLigneCommande(self):
    if self.fichierIn=="" and self.MeshIn=="":
      QMessageBox.critical(self, "Mesh", "select an input mesh")
      return False
    if self.__selectedMesh is not None: self.prepareFichier()
    if not (os.path.isfile(self.fichierIn)):
      QMessageBox.critical(self, "File", "unable to read GMF Mesh in "+str(self.fichierIn))
      return False
    
    self.commande=""
    selected_index = self.COB_Remesher.currentIndex()
    if selected_index == REMESHER_DICT['MMGS']:
      self.commande = "mmgs_O3"
    elif selected_index == REMESHER_DICT['MMG2D']:
      self.commande = "mmg2d_O3"
    elif selected_index == REMESHER_DICT['MMG3D']:
      self.commande = "mmg3d_O3"
    else:
      self.commande = "mmgs_O3"

    deb=os.path.splitext(self.fichierIn)
    self.fichierOut=deb[0] + "_output.mesh"
    
    for elt in self.sandboxes:
      self.commande+=' ' + elt[0].text() + ' ' + elt[1].text()
    
    if not self.CB_InsertEdge.isChecked() : self.commande+=" -noinsert"
    if not self.CB_SwapEdge.isChecked()  : self.commande+=" -noswap"
    if not self.CB_MoveEdge.isChecked()  : self.commande+=" -nomove"
    if self.SP_Geomapp.value() != 0.01 : self.commande+=" -hausd %f"%self.SP_Geomapp.value()
    self.commande+=" -hmin %f"   %self.SP_Hmin.value()
    self.commande+=" -hmax %f"   %self.SP_Hmax.value()
    if self.SP_Gradation.value() != 1.3   : self.commande+=" -hgrad %f"  %self.SP_Gradation.value()

    self.commande+=' -in "'  + self.fichierIn +'"'
    self.commande+=' -out "' + self.fichierOut +'"'

    if verbose: print("INFO: MMG command:\n  %s\n*WARNING* Copy-paste the command line in your study if you want to dump it." % self.commande)
    return True

  def clean(self):
    if self.values is None and self.currentName != "" and self.COB_Remesher.currentIndex() == REMESHER_DICT['MMGS']:
      if self.fichierIn != "":
        cpy = self.fichierIn
        self.GenMedFromAny(self.fichierIn)
        self.values = Values(self.fichierIn, 0, self.currentName)
        self.fichierIn = cpy
      elif self.MeshIn != "":
        self.values = Values(self.MeshIn, 0, self.currentName)

    if self.values is not None:
      self.values.ComputeNewDefaultValues()
      self.SP_Geomapp.setProperty("value", self.values.geomapp)
      self.SP_Gradation.setProperty("value", self.values.hgrad)
      self.SP_Hmin.setProperty("value", self.values.hmin)
      self.SP_Hmax.setProperty("value", self.values.hmax)
      self.values.DeleteMesh()

    else: # No file provided, default from MMG
      self.SP_Geomapp.setProperty("value", 0.01)
      self.SP_Gradation.setProperty("value", 1.3)
      self.SP_Hmin.setProperty("value", 0.01)
      self.SP_Hmax.setProperty("value", 10)
    self.values = None
    self.CB_InsertEdge.setChecked(True)
    self.CB_MoveEdge.setChecked(True)
    self.CB_SwapEdge.setChecked(True)
    self.CB_RepairBeforeCompute.setChecked(True)
    self.CB_RepairOnly.setChecked(False)
    self.CB_GenRepair.setChecked(False)
    #self.COB_Remesher.setCurrentIndex(REMESHER_DICT['MMGS'])

    from PyQt5 import QtCore, QtGui, QtWidgets
    _translate = QtCore.QCoreApplication.translate
    for i in reversed(range(self.gridLayout_5.count())):
      widget = self.gridLayout_5.takeAt(i).widget()
      if widget is not None:
        widget.setParent(None)

    self.LE_SandboxR_1 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
    self.LE_SandboxR_1.setMinimumSize(QtCore.QSize(0, 30))
    self.LE_SandboxR_1.setObjectName("LE_SandboxR_1")
    self.gridLayout_5.addWidget(self.LE_SandboxR_1, 1, 1, 1, 1)

    self.LE_SandboxL_1 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
    self.LE_SandboxL_1.setMinimumSize(QtCore.QSize(0, 30))
    self.LE_SandboxL_1.setObjectName("LE_SandboxL_1")
    self.gridLayout_5.addWidget(self.LE_SandboxL_1, 1, 0, 1, 1)

    self.label_3 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
    self.label_3.setObjectName("label_3")
    self.gridLayout_5.addWidget(self.label_3, 0, 1, 1, 1)

    self.label_2 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
    self.label_2.setObjectName("label_2")
    self.gridLayout_5.addWidget(self.label_2, 0, 0, 1, 1)

    spacerItem16 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    self.gridLayout_5.addItem(spacerItem16, 2, 0, 1, 1)

    spacerItem17 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    self.gridLayout_5.addItem(spacerItem17, 2, 1, 1, 1)

    self.gridLayout_5.setRowStretch(0,0)
    self.gridLayout_5.setRowStretch(1,0)
    self.gridLayout_5.setRowStretch(2,0)

    self.label_3.setText(_translate("MyPlugDialog", "Value"))
    self.label_2.setText(_translate("MyPlugDialog", "Parameter"))

    self.LE_SandboxL_1.setText("")
    self.LE_SandboxR_1.setText("")
    self.sandboxes = [(self.LE_SandboxL_1, self.LE_SandboxR_1)]

    #self.PBMeshSmeshPressed() #do not that! problem if done in load surfopt hypo from object browser
    self.TWOptions.setCurrentIndex(0) # Reset current active tab to the first tab
    value = self.SP_Hmin.value()
    self.UpdateHminDecimals(value)
    value = self.SP_Hmax.value()
    self.UpdateHmaxDecimals(value)

__dialog=None
def getDialog():
  """
  This function returns a singleton instance of the plugin dialog.
  It is mandatory in order to call show without a parent ...
  """
  global __dialog
  if __dialog is None:
    __dialog = MeshBooleanDialog()
  #else :
  #  __dialog.clean()
  return __dialog
