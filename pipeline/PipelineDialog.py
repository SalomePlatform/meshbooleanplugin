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
from MeshBooleanPlugin.myViewText import MyViewText
from qtsalome import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from MeshBooleanPlugin.pipeline.pipeline_ui import Ui_PipelineDialog
from MeshBooleanPlugin.add_pipeline_element.add_dialog import AddDialog

verbose = True

REMESHER_DICT = { 'MMGS' : 0, 'MMG2D' : 1, 'MMG3D' : 2 }

class PipelineDialog(Ui_PipelineDialog,QWidget):
  """
  """
  def __init__(self):
    QWidget.__init__(self)
    self.setWindowFlags(self.windowFlags())
    self.setupUi(self)
    self.connecterSignaux()
    self.fichierIn=""
    self.fichierOut=""
    self.MeshIn=""
    self.commande=""
    self.num=1
    self.__selectedMesh=None
    self.isFile = False
    self.currentName = ""

    # complex with QResources: not used
    # The icon are supposed to be located in the $SMESH_ROOT_DIR/share/salome/resources/smesh folder,
    # other solution could be in the same folder than this python module file:
    # iconfolder=os.path.dirname(os.path.abspath(__file__))

    self.resize(800, 600)
    self.NbOptParam = 0


  def connecterSignaux(self) :
    self.PB_Cancel.clicked.connect(self.PBCancelPressed)
    self.PB_Help.clicked.connect(self.PBHelpPressed)
    self.PB_Add.clicked.connect(self.PBAddPipelineElement)

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

  def PBCancelPressed(self):
    self.close()

  def PBAddPipelineElement(self):
      self.maFenetre = AddDialog()
      pass

__dialog=None
def getDialog():
  """
  This function returns a singleton instance of the plugin dialog.
  It is mandatory in order to call show without a parent ...
  """
  global __dialog
  if __dialog is None:
    __dialog = PipelineDialog()
  #else :
  #  __dialog.clean()
  return __dialog
