from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QTreeView, QVBoxLayout, QWidget

from MeshBooleanPlugin.pipeline.PipelineNode import PipelineNode
from MeshBooleanPlugin.pipeline.BooleanNode import BooleanNode
from MeshBooleanPlugin.pipeline.RemeshingNode import RemeshingNode
from MeshBooleanPlugin.pipeline.FillingNode import FillingNode

class CustomTreeView(QTreeView):
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            item = self.model().itemFromIndex(index)
            if item and isinstance(item, PipelineNode):
                item.contextMenuEvent(event)

        super().mousePressEvent(event)

class PipelineTreeModel(QStandardItemModel):
    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root_node = root
        if root is None:
            return
        self.appendRow(self.root_node)
        self.build_tree(root, self.root_node)

    def build_tree(self, node, item):
        for child_node in node.children:
            item.appendRow(child_node)
            self.build_tree(child_node, child_node)

model = PipelineTreeModel(None)
class PipelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tree_view = CustomTreeView()
        self.tree_view.setModel(model)
        self.tree_view.setAnimated(True)
        self.tree_view.setHeaderHidden(True)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tree_view)

        # BooleanNode, FillingNode and Remeshing nodes are implementations of
        # PipelineNode. They will have behavior later.
        self.root_node = PipelineNode(self, 'Root')
        child2_node = BooleanNode(self, 'Boolean_1')
        self.root_node.add_child(child2_node)
        child1_node = RemeshingNode(self, 'Remeshing_1')
        self.root_node.add_child(child1_node)
        child2_node = FillingNode(self, 'Filling_1')
        self.root_node.add_child(child2_node)
        self.update_view()


    def update_view(self):
        self.layout.removeWidget(self.tree_view)
        model = PipelineTreeModel(self.root_node)
        self.tree_view.setModel(model)
        self.tree_view.expandAll()
        self.layout.addWidget(self.tree_view)
        self.layout.update()
