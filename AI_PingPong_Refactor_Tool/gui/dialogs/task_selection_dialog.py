"""
Task Selection Dialog - Sélection tasks depuis parsing AI.
Extrait de main.py _show_tasks_dialog() (L2033-2102).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QWidget, QCheckBox, QFrame
)
from PySide6.QtCore import Signal


class TaskSelectionDialog(QDialog):
    """
    Dialog pour sélectionner tasks parsées depuis AI.
    Code extrait SANS modification de main.py.
    """
    
    tasks_selected = Signal(list)  # Émis avec tasks sélectionnées
    
    def __init__(self, parent, tasks):
        super().__init__(parent)
        self.tasks = tasks
        self.setWindowTitle(f"📋 AI Suggested {len(tasks)} Task(s)")
        self.setMinimumSize(800, 600)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI (COPIÉ de _show_tasks_dialog L2033-2102)."""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select tasks to add to your backlog:"))
        
        # Scrollable area for tasks
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.task_checkboxes = []
        
        for task in self.tasks:
            # Task card
            card = QWidget()
            card.setStyleSheet("background: #f5f5f5; border-radius: 5px; padding: 10px;")
            card_layout = QVBoxLayout(card)
            
            # Checkbox for task
            task_title = task.get('title', 'Untitled Task')
            task_type = task.get('type', 'unknown')
            priority = task.get('priority', 'medium')
            
            checkbox = QCheckBox(f"[{priority.upper()}] {task_title}")
            checkbox.setChecked(True)
            checkbox.setStyleSheet("font-weight: bold; font-size: 12pt;")
            card_layout.addWidget(checkbox)
            
            # Description
            desc = task.get('description', 'No description')
            desc_label = QLabel(f"📝 {desc}")
            desc_label.setWordWrap(True)
            card_layout.addWidget(desc_label)
            
            # Associated methods
            methods = task.get('methods', [])
            if methods:
                methods_text = "🔧 Methods: " + ", ".join([f"{m['class']}.{m['method']}" for m in methods])
                methods_label = QLabel(methods_text)
                methods_label.setStyleSheet("color: #666; font-size: 9pt;")
                card_layout.addWidget(methods_label)
            
            scroll_layout.addWidget(card)
            self.task_checkboxes.append((checkbox, task))
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        btn_add = QPushButton("✅ Add Selected Tasks")
        btn_add.clicked.connect(self.accept)
        button_layout.addWidget(btn_add)
        
        btn_cancel = QPushButton("❌ Cancel")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)
    
    def get_selected_tasks(self):
        """Retourne tasks sélectionnées."""
        return [task for checkbox, task in self.task_checkboxes if checkbox.isChecked()]
