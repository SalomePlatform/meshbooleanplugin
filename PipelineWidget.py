from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QFont, QPen
from PyQt5.QtWidgets import *
from qtsalome import *
from PipelineNode import PipelineNode
from enum import Enum
from BooleanNode import BooleanNode
from RemeshingNode import RemeshingNode
from FillingNode import FillingNode
import sys

class Type(Enum):
    BOOLEAN=1
    REMESHING=2
    FILLING=3

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
        self.appendRow(self.root_node)
        self.build_tree(root, self.root_node)

    def build_tree(self, node, item):
        for child_node in node.children:
            item.appendRow(child_node)
            self.build_tree(child_node, child_node)

class PipelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tree_view = CustomTreeView()
        self.tree_view.setAnimated(True)
        self.tree_view.setHeaderHidden(True)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tree_view)

        boolean_type = Type.BOOLEAN
        remeshing_type = Type.REMESHING
        filling_type = Type.FILLING

        # BooleanNode, FillingNode and Remeshing nodes are class that contains a name
        # They will have behavior later.
        first_node = BooleanNode('Root')
        root_node = PipelineNode(boolean_type, first_node)

        node1 = RemeshingNode('child1')
        child1 = PipelineNode(remeshing_type, node1)
        root_node.add_child(child1)

        node2 = FillingNode('child2')
        child2 = PipelineNode(remeshing_type, node2)
        root_node.add_child(child2)

        model = PipelineTreeModel(root_node)
        self.tree_view.setModel(model)
        self.tree_view.expandAll()
