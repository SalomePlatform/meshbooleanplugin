import os
from MeshBooleanPlugin.add_pipeline_element.AddDialog_ui import Ui_AddDialog
from qtsalome import *

class AddDialog(Ui_AddDialog, QWidget):
  def __init__(self, parent=None):
    QWidget.__init__(self, parent)
    self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
    self.setupUi(self)
    self.resize( QSize(1000,600).expandedTo(self.minimumSizeHint()) )
    self.connecterSignaux()
    self.iconfolder=os.path.join(os.environ["SMESH_ROOT_DIR"], "share", "salome", "resources", "smesh")
    icon = QIcon()
    icon.addFile(os.path.join(self.iconfolder,"select1.png"))
    self.PB_MeshSmesh_L.setIcon(icon)
    self.PB_MeshSmesh_R.setIcon(icon)
    self.PB_MeshSmesh_Remeshing.setIcon(icon)
    self.PB_MeshSmesh_Filling.setIcon(icon)
    self.PB_MeshSmesh_L.setToolTip("source mesh from Salome Object Browser")
    self.PB_MeshSmesh_R.setToolTip("source mesh from Salome Object Browser")
    self.PB_MeshSmesh_Remeshing.setToolTip("source mesh from Salome Object Browser")
    self.PB_MeshSmesh_Filling.setToolTip("source mesh from Salome Object Browser")
    icon = QIcon()
    icon.addFile(os.path.join(self.iconfolder,"open.png"))
    self.PB_MeshFile_L.setIcon(icon)
    self.PB_MeshFile_R.setIcon(icon)
    self.PB_MeshFile_Remeshing.setIcon(icon)
    self.PB_MeshFile_Filling.setIcon(icon)
    self.PB_MeshFile_L.setToolTip("source mesh from a file in disk")
    self.PB_MeshFile_R.setToolTip("source mesh from a file in disk")
    self.PB_MeshFile_Remeshing.setToolTip("source mesh from a file in disk")
    self.PB_MeshFile_Filling.setToolTip("source mesh from a file in disk")
    self.show()

  def connecterSignaux(self) :
    self.PB_Cancel.clicked.connect(self.PBCancelPressed)
    self.PB_Help.clicked.connect(self.PBHelpPressed)

  def PBHelpPressed(self):
    QMessageBox.about(None, "About this Dialog",
            """
This Dialog allows you to add an element to the lesh pipeline
of this plugin. You can add:
- A boolean operation:
    It requires you to choose two input meshes, a boolean
    operator, and a boolean engine. It displays some
    information about the engine that you chose.

- A remeshing with MMG:
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

- A filling with Gmsh:
    This tool can fill surface meshes with tetrahedra.

Once all the needed fields filled, press Aply to compute the
result of the pipeline element.
            """)

  def PBCancelPressed(self):
    self.close()
