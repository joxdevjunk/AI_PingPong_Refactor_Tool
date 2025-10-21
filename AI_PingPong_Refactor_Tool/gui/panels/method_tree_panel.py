"""
Method Tree Panel - Left panel avec arborescence des méthodes.
Extrait de main.py lignes 290-319, 1162-1239.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QTreeWidgetItemIterator
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import List


class MethodTreePanel(QWidget):
    """
    Panel gauche: Tree File → Class → Method.
    Code extrait SANS modification de main.py.
    """
    
    # Signals émis par le panel
    selection_changed = Signal(int)  # Nombre de méthodes sélectionnées
    
    def __init__(self):
        super().__init__()
        self._all_tasks = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI (COPIÉ de _create_left_panel L290-319)."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("📋 Select Methods")
        title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 8px;")
        layout.addWidget(title)
        
        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderLabels(["Component", "Type", "Line", "docstring"])
        self.task_tree.setMinimumWidth(600)
        self.task_tree.setColumnWidth(0, 200)
        self.task_tree.setColumnWidth(1, 60)
        self.task_tree.setColumnWidth(2, 60)
        self.task_tree.setColumnWidth(3, 300)
        self.task_tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.task_tree)
        
        self.lbl_selection = QLabel("0 tasks selected")
        self.lbl_selection.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(self.lbl_selection)
    
    def populate(self, all_tasks: List):
        """Populate tree (COPIÉ de _populate_task_tree L1162-1239)."""
        self.task_tree.clear()
        self._all_tasks = list(all_tasks)
        
        files_dict = {}
        for idx, task in enumerate(self._all_tasks):
            file_path = task.file
            if file_path not in files_dict:
                files_dict[file_path] = []
            files_dict[file_path].append((idx, task))
        
        for file_path, tasks_with_ids in sorted(files_dict.items()):
            file_item = QTreeWidgetItem(self.task_tree, [file_path, 'File', '', ''])
            file_item.setFlags(file_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            file_item.setCheckState(0, Qt.Unchecked)
            
            classes_dict = {}
            for task_id, task in tasks_with_ids:
                class_name = task.class_name
                if class_name not in classes_dict:
                    classes_dict[class_name] = []
                classes_dict[class_name].append((task_id, task))
            
            for class_name, methods_with_ids in sorted(classes_dict.items()):
                class_item = QTreeWidgetItem(file_item, [class_name, 'Class', '', ''])
                class_item.setFlags(class_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
                class_item.setCheckState(0, Qt.Unchecked)
                
                for task_id, method in sorted(methods_with_ids, key=lambda x: x[1].lineno):
                    method_text = f"{method.method_name}()"
                    
                    docstring = getattr(method, 'docstring', None) or 'No docstring'
                    if docstring and docstring != 'No docstring':
                        first_line = docstring.split('\n')[0].strip()
                        first_line = first_line.replace('"""', '').replace("'''", '').strip()
                        if len(first_line) > 60:
                            first_line = first_line[:57] + "..."
                        docstring_display = first_line
                    else:
                        docstring_display = "⚠️ No docstring"
                    
                    method_item = QTreeWidgetItem(class_item, [
                        method_text,
                        'Method',
                        str(method.lineno),
                        docstring_display
                    ])
                    method_item.setFlags(method_item.flags() | Qt.ItemIsUserCheckable)
                    method_item.setCheckState(0, Qt.Unchecked)
                    
                    if docstring and docstring != 'No docstring':
                        method_item.setToolTip(3, docstring)
                        method_item.setToolTip(0, f"{method.method_name}\n\n{docstring}")
                    
                    if docstring_display == "⚠️ No docstring":
                        method_item.setForeground(3, QColor(255, 100, 100))
                    
                    method_item.setData(0, Qt.UserRole, task_id)
        
        self.task_tree.expandAll()
    
    def _on_item_changed(self, item, column):
        """Handler when checkbox changed."""
        iterator = QTreeWidgetItemIterator(self.task_tree, QTreeWidgetItemIterator.Checked)
        count = 0
        while iterator.value():
            item = iterator.value()
            if item.data(0, Qt.UserRole) is not None:
                count += 1
            iterator += 1
        
        self.lbl_selection.setText(f"{count} method(s) selected")
        
        for task in self._all_tasks:
            task.selected = False
        
        iterator = QTreeWidgetItemIterator(self.task_tree, QTreeWidgetItemIterator.Checked)
        while iterator.value():
            item = iterator.value()
            task_id = item.data(0, Qt.UserRole)
            if task_id is not None and task_id < len(self._all_tasks):
                self._all_tasks[task_id].selected = True
            iterator += 1
        
        self.selection_changed.emit(count)
    
    def get_selected_tasks(self) -> List:
        """Retourne les tasks sélectionnées."""
        return [task for task in self._all_tasks if task.selected]
