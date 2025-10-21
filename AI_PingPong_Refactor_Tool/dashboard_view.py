from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QScrollArea, QGridLayout, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor

class TaskCard(QFrame):
    """Card visuelle pour une task - CLIQUABLE."""
    
    clicked = Signal(object)  # Émet la task quand cliqué
    
    def __init__(self, task):
        super().__init__()
        self.task = task
        self._setup_ui()
        
        # Style card
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setCursor(Qt.PointingHandCursor)
        
        # Couleur priorité
        priority_colors = {
            'high': '#ffebee',
            'medium': '#fff3e0',
            'low': '#e8f5e9'
        }
        color = priority_colors.get(task['priority'], '#f5f5f5')
        self.setStyleSheet(f"""
            TaskCard {{
                background: {color};
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 12px;
                margin: 4px;
            }}
            TaskCard:hover {{
                border-color: #2196F3;
                background: white;
            }}
        """)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header: priorité + status
        header = QHBoxLayout()
        
        priority_icon = {"high": "🔴", "medium": "🟠", "low": "🟢"}[self.task['priority']]
        status_icon = {"todo": "📝", "in_progress": "⚙️", "done": "✅"}[self.task['status']]
        
        header.addWidget(QLabel(f"{priority_icon} {status_icon}"))
        header.addStretch()
        
        layout.addLayout(header)
        
        # Title (bold)
        title = QLabel(self.task['title'])
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setWordWrap(True)
        layout.addWidget(title)
        
        # Description (preview)
        desc = self.task['description'][:80] + ("..." if len(self.task['description']) > 80 else "")
        desc_label = QLabel(desc)
        desc_label.setStyleSheet("color: #666; font-size: 9pt;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Footer: méthodes count
        footer = QLabel(f"🔧 {len(self.task.get('methods', []))} method(s)")
        footer.setStyleSheet("color: #999; font-size: 8pt; margin-top: 8px;")
        layout.addWidget(footer)
    
    def mousePressEvent(self, event):
        """Émet signal quand cliqué."""
        self.clicked.emit(self.task)


class DashboardView(QWidget):
    """Vue Dashboard moderne avec cards."""
    
    task_clicked = Signal(object)
    
    def __init__(self):
        super().__init__()
        self.tasks = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # === TOP: Overview Stats ===
        stats_widget = self._create_stats_panel()
        layout.addWidget(stats_widget)
        
        # === MIDDLE: Tasks Board (scrollable) ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.board_widget = QWidget()
        self.board_layout = QGridLayout(self.board_widget)
        self.board_layout.setSpacing(10)
        
        scroll.setWidget(self.board_widget)
        layout.addWidget(scroll, 1)
    
    def _create_stats_panel(self):
        """Crée panel statistiques."""
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                padding: 20px;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Stats
        self.lbl_high = QLabel("🔴 High: 0")
        self.lbl_medium = QLabel("🟠 Medium: 0")
        self.lbl_low = QLabel("🟢 Low: 0")
        
        layout.addWidget(self.lbl_high)
        layout.addWidget(self.lbl_medium)
        layout.addWidget(self.lbl_low)
        layout.addStretch()
        
        self.lbl_todo = QLabel("📝 Todo: 0")
        self.lbl_progress = QLabel("⚙️ Progress: 0")
        self.lbl_done = QLabel("✅ Done: 0")
        
        layout.addWidget(self.lbl_todo)
        layout.addWidget(self.lbl_progress)
        layout.addWidget(self.lbl_done)
        
        return panel
    
    def set_tasks(self, tasks):
        """Met à jour dashboard avec tasks."""
        self.tasks = tasks
        self._refresh()
    
    def _refresh(self):
        """Rafraîchit affichage."""
        # Clear board
        for i in reversed(range(self.board_layout.count())): 
            self.board_layout.itemAt(i).widget().deleteLater()
        
        # Update stats
        high = sum(1 for t in self.tasks if t['priority'] == 'high')
        medium = sum(1 for t in self.tasks if t['priority'] == 'medium')
        low = sum(1 for t in self.tasks if t['priority'] == 'low')
        
        todo = sum(1 for t in self.tasks if t['status'] == 'todo')
        progress = sum(1 for t in self.tasks if t['status'] == 'in_progress')
        done = sum(1 for t in self.tasks if t['status'] == 'done')
        
        self.lbl_high.setText(f"🔴 High: {high}")
        self.lbl_medium.setText(f"🟠 Medium: {medium}")
        self.lbl_low.setText(f"🟢 Low: {low}")
        self.lbl_todo.setText(f"📝 Todo: {todo}")
        self.lbl_progress.setText(f"⚙️ Progress: {progress}")
        self.lbl_done.setText(f"✅ Done: {done}")
        
        # Add cards (3 columns grid)
        for i, task in enumerate(sorted(self.tasks, key=lambda t: t['created_at'], reverse=True)):
            card = TaskCard(task)
            card.clicked.connect(self.task_clicked.emit)
            
            row = i // 3
            col = i % 3
            self.board_layout.addWidget(card, row, col)
