"""
Refactoring Dialog - Preview tasks refactoring depuis AI.
Extrait de main.py _show_refactoring_tasks_dialog() (L1917-2031).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QWidget, QCheckBox, QFrame
)
from PySide6.QtCore import Signal


class RefactoringDialog(QDialog):
    """
    Dialog pour preview tasks refactoring.
    Code extrait SANS modification de main.py.
    """
    
    tasks_selected = Signal(list)
    
    def __init__(self, parent, tasks):
        super().__init__(parent)
        self.tasks = tasks
        self.setWindowTitle(f"Refactoring Tasks ({len(tasks)} found)")
        self.setMinimumSize(800, 600)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI (COPIÉ de _show_refactoring_tasks_dialog L1917-2031)."""
        layout = QVBoxLayout(self)
        
        # Label info
        info_label = QLabel(f"✨ {len(self.tasks)} refactoring tasks extracted from AI analysis")
        info_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: #4CAF50;")
        layout.addWidget(info_label)
        
        # Stats
        stats = {
            'critical': sum(1 for t in self.tasks if t['priority'] == 'critical'),
            'high': sum(1 for t in self.tasks if t['priority'] == 'high'),
            'medium': sum(1 for t in self.tasks if t['priority'] == 'medium'),
            'quick_wins': sum(1 for t in self.tasks if 'quick-win' in t.get('tags', [])),
            'epics': sum(1 for t in self.tasks if t['category'] == 'epic')
        }
        
        stats_text = (
            f"🔴 Critical: {stats['critical']} | "
            f"🟠 High: {stats['high']} | "
            f"🟡 Medium: {stats['medium']} | "
            f"⚡ Quick Wins: {stats['quick_wins']} | "
            f"📦 Epics: {stats['epics']}"
        )
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("color: #888; font-size: 10pt;")
        layout.addWidget(stats_label)
        
        # Scroll area pour tasks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Checkboxes pour chaque task
        self.task_checkboxes = []
        
        for task in self.tasks:
            # Container pour task
            task_container = QFrame()
            task_container.setFrameStyle(QFrame.Box)
            task_container.setStyleSheet("""
                QFrame {
                    background: #2b2b2b;
                    border: 1px solid #444;
                    border-radius: 4px;
                    padding: 8px;
                    margin: 4px 0;
                }
            """)
            task_layout = QVBoxLayout(task_container)
            
            # Checkbox avec titre
            checkbox = QCheckBox(task['title'])
            checkbox.setChecked(True)  # Toutes cochées par défaut
            checkbox.setStyleSheet("font-weight: bold; font-size: 11pt;")
            self.task_checkboxes.append((checkbox, task))
            task_layout.addWidget(checkbox)
            
            # Metadata
            meta_text = f"Priority: {task['priority'].upper()} | Effort: {task['effort']} | Category: {task['category']}"
            meta_label = QLabel(meta_text)
            meta_label.setStyleSheet("color: #888; font-size: 9pt; margin-left: 20px;")
            task_layout.addWidget(meta_label)
            
            # Description (première ligne seulement)
            desc_preview = task['description'].split('\n')[0][:150]
            if len(task['description']) > 150:
                desc_preview += "..."
            desc_label = QLabel(desc_preview)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #aaa; font-size: 9pt; margin-left: 20px;")
            task_layout.addWidget(desc_label)
            
            scroll_layout.addWidget(task_container)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Boutons actions
        button_layout = QHBoxLayout()
        
        btn_select_all = QPushButton("✓ Select All")
        btn_select_all.clicked.connect(lambda: [cb.setChecked(True) for cb, _ in self.task_checkboxes])
        button_layout.addWidget(btn_select_all)
        
        btn_select_none = QPushButton("✗ Select None")
        btn_select_none.clicked.connect(lambda: [cb.setChecked(False) for cb, _ in self.task_checkboxes])
        button_layout.addWidget(btn_select_none)
        
        button_layout.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        btn_add = QPushButton("✨ Add Selected Tasks")
        btn_add.setStyleSheet("background: #4CAF50; color: white; font-weight: bold;")
        btn_add.clicked.connect(self.accept)
        button_layout.addWidget(btn_add)
        
        layout.addLayout(button_layout)
    
    def get_selected_tasks(self):
        """Retourne tasks sélectionnées."""
        return [task for checkbox, task in self.task_checkboxes if checkbox.isChecked()]
