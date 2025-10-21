"""
Methods Selector Panel - Tab avec tree et statistiques.
Extrait de main.py _create_methods_tab().
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QTreeWidget, QSplitter
)
from PySide6.QtCore import Signal


class MethodsSelectorPanel(QWidget):
    """Panel affichant tree méthodes + statistiques."""
    
    # Signals
    analyze_requested = Signal()
    file_summary_requested = Signal()
    decorators_requested = Signal()
    
    def __init__(self, task_tree=None, stats_labels=None, parent=None):
        super().__init__(parent)
        self.task_tree = task_tree
        self.stats_labels = stats_labels or {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup panel layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        btn_analyze = QPushButton("🔍 Analyze Project")
        btn_analyze.clicked.connect(self.analyze_requested.emit)
        toolbar.addWidget(btn_analyze)
        
        btn_file_summary = QPushButton("📄 File Summary")
        btn_file_summary.setToolTip("Generate summary for selected file")
        btn_file_summary.clicked.connect(self.file_summary_requested.emit)
        toolbar.addWidget(btn_file_summary)
        
        btn_decorators = QPushButton("🎨 Add Decorators")
        btn_decorators.setToolTip("Apply debug decorators to selected methods")
        btn_decorators.clicked.connect(self.decorators_requested.emit)
        toolbar.addWidget(btn_decorators)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Splitter avec tree + stats
        splitter = QSplitter()
        
        # Tree (réutilise celle de main.py)
        if self.task_tree:
            splitter.addWidget(self.task_tree)
        
        # Stats panel
        stats_widget = self._create_stats_panel()
        splitter.addWidget(stats_widget)
        
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)
    
    def _create_stats_panel(self):
        """Crée panel statistiques."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("<b>📊 Project Statistics</b>"))
        
        # Créer labels stats
        self.lbl_total_files = QLabel("Files: 0")
        self.lbl_total_classes = QLabel("Classes: 0")
        self.lbl_total_methods = QLabel("Methods: 0")
        self.lbl_selected = QLabel("Selected: 0")
        
        layout.addWidget(self.lbl_total_files)
        layout.addWidget(self.lbl_total_classes)
        layout.addWidget(self.lbl_total_methods)
        layout.addWidget(self.lbl_selected)
        
        layout.addStretch()
        
        return widget
    
    def update_stats(self, total_files=0, total_classes=0, total_methods=0, selected=0):
        """Update stats display."""
        self.lbl_total_files.setText(f"Files: {total_files}")
        self.lbl_total_classes.setText(f"Classes: {total_classes}")
        self.lbl_total_methods.setText(f"Methods: {total_methods}")
        self.lbl_selected.setText(f"Selected: {selected}")
