# -*- coding: utf-8 -*-
# Copyright (C) 2006-2023  EDF
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

# if you already have plugins defined in a salome_plugins.py file, add this file at the end.
# if not, copy this file as ${HOME}/Plugins/smesh_plugins.py or ${APPLI}/Plugins/smesh_plugins.py
def MeshBoolean(context):
  # get context study, salomeGui
  study = context.study
  sg = context.sg
  
  import os
  import subprocess
  import tempfile
  import platform
  from qtsalome import QFileDialog, QMessageBox
  
  import meshbooleanplugin.mesh_boolean_dialog as mesh_boolean_dialog
  items = []
  if platform.system() == "Windows" :
    items = ['igl', 'cork', 'vtk']
  else:
    if 'CGAL_ROOT_DIR' in os.environ:
      items.append('CGAL')
    if 'LIBIGL_ROOT_DIR' in os.environ:
      items.append('igl')
    items.append('vtk')
    if 'IRMB_ROOT_DIR' in os.environ:
      items.append('irmb')
    if 'CORK_ROOT_DIR' in os.environ:
      items.append('cork')
    if 'MCUT_ROOT_DIR' in os.environ:
      items.append('mcut')
  #
  window = mesh_boolean_dialog.getDialog()

  #clear the engine before refilling it each time we click on mesh boolean operations
  window.COB_Engine.clear()
  for item in items:
    window.COB_Engine.addItem(item)
  window.show()
