from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QStandardItem
from PyQt5.QtCore import Qt, QTimer

class PipelineNode(QStandardItem):
    # Should be abstract but not sure if it is possible
    def __init__(self, parent_widget, name):
        super().__init__(name)
        self.name = name
        self.children = []
        self.parent_node = None
        self.parent_widget = parent_widget

    def contextMenuEvent(self, event):
        pass

    def add_child(self, child):
        self.children.append(child)
        child.parent_node = self

    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)
            self.parent_widget.update_view()
