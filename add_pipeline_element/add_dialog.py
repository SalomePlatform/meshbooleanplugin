from MeshBooleanPlugin.add_pipeline_element.AddDialog_ui import Ui_AddDialog
from qtsalome import *

class AddDialog(Ui_AddDialog, QWidget):
  def __init__(self, parent=None):
    QWidget.__init__(self, parent)
    self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
    self.setupUi(self)
    self.resize( QSize(1000,600).expandedTo(self.minimumSizeHint()) )
    self.connecterSignaux()
    self.show()

  def connecterSignaux(self) :
    self.PB_Cancel.clicked.connect(self.PBCancelPressed)
    self.PB_Help.clicked.connect(self.PBHelpPressed)

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
