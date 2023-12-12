from PyQt5.QtWidgets import *
from qtsalome import *
from PyQt5.QtCore import Qt

class PipelineNode(QStandardItem):
    def __init__(self, paramtype, value):
        super().__init__(value.name)
        self.type = paramtype
        self.value = value
        self.children = []

    def contextMenuEvent(self, event):
        menu = QMenu()
        action = QAction(None)
        action.triggered.connect(self.handleCustomAction)
        menu.addAction(action)

        menu.exec_(event.globalPos())

    def add_child(self, node):
        self.children.append(node)

    def handleCustomAction(self):
        print(f"Custom action triggered for node: {self.value.name}")
