"""
Task Board Panel - Dashboard avec cards tasks visuelles.
Extrait de main.py _create_center_panel (partie tasks board).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QGridLayout, QFrame
)
from PySide6.QtCore import Signal


class TaskBoardPanel(QWidget):
    """
    Panel tasks board: Dashboard avec cards visuelles.
    Code extrait SANS modification de main.py.
    """
    
    # Signals
    task_card_clicked = Signal(dict)  # Émis quand card cliquée
    new_task_requested = Signal()     # Émis quand bouton NEW cliqué
    
    def __init__(self):
        super().__init__()
        self.tasks = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI (COPIÉ de _create_center_panel L321-612 partie tasks)."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # === STATS PANEL (BRUTALISTE) ===
        stats_frame = QFrame()
        stats_frame.setFixedHeight(32)
        stats_frame.setStyleSheet("""
            QFrame {
                background: #0d1117;
                border-top: 1px solid #30363d;
                border-bottom: 1px solid #30363d;
            }
        """)
        
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(12)
        stats_layout.setContentsMargins(12, 0, 12, 0)
        
        # Priority labels
        self.lbl_high = QLabel("H:0")
        self.lbl_high.setStyleSheet("color: #ff6b6b; font: 10pt 'Consolas';")
        
        self.lbl_medium = QLabel("M:0")
        self.lbl_medium.setStyleSheet("color: #ffa500; font: 10pt 'Consolas';")
        
        self.lbl_low = QLabel("L:0")
        self.lbl_low.setStyleSheet("color: #51cf66; font: 10pt 'Consolas';")
        
        stats_layout.addWidget(self.lbl_high)
        stats_layout.addWidget(self.lbl_medium)
        stats_layout.addWidget(self.lbl_low)
        
        # Separator
        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #30363d;")
        stats_layout.addWidget(sep1)
        
        # Status labels
        self.lbl_todo = QLabel("TODO:0")
        self.lbl_todo.setStyleSheet("color: #8b949e; font: 10pt 'Consolas';")
        
        self.lbl_progress = QLabel("PROG:0")
        self.lbl_progress.setStyleSheet("color: #58a6ff; font: 10pt 'Consolas';")
        
        self.lbl_done = QLabel("DONE:0")
        self.lbl_done.setStyleSheet("color: #3fb950; font: 10pt 'Consolas';")
        
        stats_layout.addWidget(self.lbl_todo)
        stats_layout.addWidget(self.lbl_progress)
        stats_layout.addWidget(self.lbl_done)
        stats_layout.addStretch()
        
        # Total
        self.lbl_total = QLabel("TOTAL:0")
        self.lbl_total.setStyleSheet("color: #c9d1d9; font: bold 10pt 'Consolas';")
        stats_layout.addWidget(self.lbl_total)
        
        # Force visibility
        stats_frame.setVisible(True)
        
        layout.addWidget(stats_frame)
        
        # === TASKS HEADER ===
        tasks_header = QHBoxLayout()
        
        tasks_label = QLabel("TASKS_CREATED")
        tasks_label.setStyleSheet(
            "font: bold 10pt 'Consolas'; color: #c9d1d9; padding: 8px;"
        )
        tasks_header.addWidget(tasks_label)
        tasks_header.addStretch()
        
        # NEW TASK button
        btn_new_task = QPushButton("[+] NEW")
        btn_new_task.setFixedHeight(28)
        btn_new_task.setToolTip("Create new task (inline editing)")
        btn_new_task.setStyleSheet("""
            QPushButton {
                background: #0d1117;
                color: #3fb950;
                border: 2px solid #3fb950;
                padding: 4px 12px;
                font: bold 9pt 'Consolas';
            }
            QPushButton:hover {
                background: #3fb950;
                color: #0d1117;
            }
        """)
        btn_new_task.clicked.connect(self._on_new_task_clicked)
        tasks_header.addWidget(btn_new_task)
        
        layout.addLayout(tasks_header)
        
        # === SCROLL AREA ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.board_widget = QWidget()
        self.board_layout = QGridLayout(self.board_widget)
        self.board_layout.setSpacing(8)
        
        scroll.setWidget(self.board_widget)
        layout.addWidget(scroll)
    
    def set_tasks(self, tasks: list):
        """Affiche tasks dans le dashboard."""
        self.tasks = tasks
        self.refresh()
    
    def refresh(self):
        """Refresh dashboard avec tasks actuelles."""
        # Clear board
        for i in reversed(range(self.board_layout.count())):
            widget = self.board_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Update stats
        self._update_stats()
        
        # TODO: Créer cards (logique complexe à extraire plus tard)
        # Pour l'instant, affiche compteurs uniquement
    
    def _update_stats(self):
        """Update stats labels."""
        high = sum(1 for t in self.tasks if t.get('priority') == 'high')
        medium = sum(1 for t in self.tasks if t.get('priority') == 'medium')
        low = sum(1 for t in self.tasks if t.get('priority') == 'low')
        
        todo = sum(1 for t in self.tasks if t.get('status') == 'todo')
        progress = sum(1 for t in self.tasks if t.get('status') == 'in_progress')
        done = sum(1 for t in self.tasks if t.get('status') == 'done')
        
        total = len(self.tasks)
        
        self.lbl_high.setText(f"H:{high}")
        self.lbl_medium.setText(f"M:{medium}")
        self.lbl_low.setText(f"L:{low}")
        
        self.lbl_todo.setText(f"TODO:{todo}")
        self.lbl_progress.setText(f"PROG:{progress}")
        self.lbl_done.setText(f"DONE:{done}")
        
        self.lbl_total.setText(f"TOTAL:{total}")
    
    def _on_new_task_clicked(self):
        """Handler bouton NEW."""
        self.new_task_requested.emit()
