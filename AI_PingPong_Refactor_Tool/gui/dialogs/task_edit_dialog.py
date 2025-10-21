"""
Task Edit Dialog - Dialog création/édition task manuelle.
Extrait de main.py create_manual_task() (L758-811).
"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QTextEdit, QComboBox, QMessageBox
)
from datetime import datetime


class TaskEditDialog(QDialog):
    """
    Dialog pour créer/éditer task manuellement.
    Code extrait SANS modification de main.py.
    """
    
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("➕ New Task" if not task else "✏️ Edit Task")
        self.setMinimumWidth(400)
        self._setup_ui()
        
        # Load task data si mode édition
        if task:
            self._load_task_data()
    
    def _setup_ui(self):
        """Setup UI (COPIÉ de create_manual_task L758-811)."""
        layout = QFormLayout(self)
        
        # Title
        self.title = QLineEdit()
        self.title.setPlaceholderText("Task title...")
        layout.addRow("Title:", self.title)
        
        # Description
        self.desc = QTextEdit()
        self.desc.setPlaceholderText("Description...")
        self.desc.setMaximumHeight(100)
        layout.addRow("Description:", self.desc)
        
        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["bug", "feature", "refactor", "docs"])
        layout.addRow("Type:", self.type_combo)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["high", "medium", "low"])
        layout.addRow("Priority:", self.priority_combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def _load_task_data(self):
        """Charge données task en mode édition."""
        if not self.task:
            return
        
        self.title.setText(self.task.get('title', ''))
        self.desc.setPlainText(self.task.get('description', ''))
        
        task_type = self.task.get('type', 'bug')
        idx = self.type_combo.findText(task_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        
        priority = self.task.get('priority', 'medium')
        idx = self.priority_combo.findText(priority)
        if idx >= 0:
            self.priority_combo.setCurrentIndex(idx)
    
    def get_task_data(self):
        """Retourne données task depuis form."""
        if not self.title.text():
            QMessageBox.warning(self, "Missing Title", "Please enter a title!")
            return None
        
        return {
            'title': self.title.text(),
            'description': self.desc.toPlainText(),
            'type': self.type_combo.currentText(),
            'priority': self.priority_combo.currentText(),
            'status': self.task.get('status', 'todo') if self.task else 'todo',
            'methods': self.task.get('methods', []) if self.task else [],
            'created_at': self.task.get('created_at', datetime.now()) if self.task else datetime.now()
        }
