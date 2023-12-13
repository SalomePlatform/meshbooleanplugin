from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QStandardItem, QIcon
from MeshBooleanPlugin.pipeline.PipelineNode import PipelineNode

class RemeshingNode(PipelineNode):
    def __init__(self, parent_widget, name):
        super().__init__(parent_widget, name)
        icon = QIcon()
        icon.addFile("mmg_logo.jpg")
        self.setIcon(icon)
        
    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = QAction(None)
        icon = QIcon()
        icon.addFile("edit.png")
        edit_action.setIcon(icon)
        edit_action.setIconText("Edit")
        edit_action.triggered.connect(self.Edit)
        menu.addAction(edit_action)

        delete_action = QAction(None)
        icon = QIcon()
        icon.addFile("edit.png")
        delete_action.setIcon(icon)
        delete_action.setIconText("Delete")
        delete_action.triggered.connect(self.Delete)
        menu.addAction(delete_action)

        menu.exec_(event.globalPos())

    def Edit(self):
        print(f"Edit triggered for Remeshing node: {self.name}")

    def Delete(self):
        print(f"Delete triggered for Remeshing node: {self.name}")
        parent_node = self.parent_node
        if parent_node is not None:
            parent_node.remove_child(self)
        del self
