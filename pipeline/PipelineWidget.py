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
        self.root_node = None
        self.update_model(root)

    def build_tree(self, node, item):
        print(node.children)
        for child_node in node.children:
            item.appendRow(child_node)
            self.build_tree(child_node, child_node)

    def clear_recursive(self, item):
        print("delete", item)
        for row in range(item.rowCount()):
            child_item = item.child(row, 0)
            if child_item is not None:
                self.clear_recursive(child_item)
            item.removeRow(row)

    def clear(self):
        self.clear_recursive(self.root_node)

    def update_model(self, root):
        self.root_node = root
        if root is None:
            return
        self.clear()
        self.appendRow(self.root_node)
        self.build_tree(root, self.root_node)

class PipelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tree_view = CustomTreeView()

        self.tree_view.setAnimated(True)
        self.tree_view.setHeaderHidden(True)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tree_view)

        # BooleanNode, FillingNode and Remeshing nodes are implementations of
        # PipelineNode. They will have behavior later.
        self.root_node = PipelineNode(self, 'Root')
        self.model = PipelineTreeModel(self.root_node)
        self.tree_view.setModel(self.model)
        selection_model = self.tree_view.selectionModel()
        selection_model.currentChanged.connect(self.set_selection)

        child2_node = BooleanNode(self, 'Boolean_1')
        self.root_node.add_child(child2_node)
        child1_node = RemeshingNode(self, 'Remeshing_1')
        self.root_node.add_child(child1_node)
        child2_node = FillingNode(self, 'Filling_1')
        self.root_node.add_child(child2_node)

        child3_node = BooleanNode(self, 'Boolean_2')
        self.root_node.add_child(child3_node)
        self.tree_view.expandAll()

        self.selected_nodes = []

    def set_selection(self, selected, deselected):
        self.selected_nodes = selected

    def update_view(self):
        self.model.update_model(self.root_node)
        self.tree_view.setModel(self.model)
