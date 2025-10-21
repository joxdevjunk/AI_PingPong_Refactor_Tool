"""
Inspector Panel - Affiche détails méthode sélectionnée.
Extrait de main.py _create_center_panel (partie inspector).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QTextEdit, QPushButton
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont


class InspectorPanel(QWidget):
    """Panel inspecteur: détails méthode + actions."""
    
    create_task_requested = Signal(dict)
    no_issue_marked = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.current_method = None
        self._setup_ui()
        self.setVisible(False)
    
    def _setup_ui(self):
        """Setup UI (COPIÉ de _create_center_panel L321-612)."""
        layout = QVBoxLayout(self)
        
        title_label = QLabel("METHOD_INSPECTOR")
        title_label.setStyleSheet("font: bold 10pt 'Consolas'; color: #58a6ff; padding: 8px;")
        layout.addWidget(title_label)
        
        inspector_frame = QFrame()
        inspector_frame.setFrameShape(QFrame.StyledPanel)
        inspector_frame.setStyleSheet("QFrame { background: #0d1117; border: 1px solid #30363d; }")
        
        inspector_layout = QVBoxLayout(inspector_frame)
        
        self.lbl_method_name = QLabel("NO_METHOD")
        self.lbl_method_name.setStyleSheet("font: bold 11pt 'Consolas'; color: #58a6ff;")
        inspector_layout.addWidget(self.lbl_method_name)
        
        self.lbl_method_file = QLabel("")
        self.lbl_method_file.setStyleSheet("font: 9pt 'Consolas'; color: #8b949e;")
        inspector_layout.addWidget(self.lbl_method_file)
        
        self.lbl_method_class = QLabel("")
        self.lbl_method_class.setStyleSheet("font: 9pt 'Consolas'; color: #8b949e;")
        inspector_layout.addWidget(self.lbl_method_class)
        
        self.lbl_method_line = QLabel("")
        self.lbl_method_line.setStyleSheet("font: 9pt 'Consolas'; color: #8b949e;")
        inspector_layout.addWidget(self.lbl_method_line)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #30363d;")
        inspector_layout.addWidget(line)
        
        sig_label = QLabel("SIGNATURE:")
        sig_label.setStyleSheet("font: bold 9pt 'Consolas'; color: #c9d1d9; margin-top: 8px;")
        inspector_layout.addWidget(sig_label)
        
        self.lbl_signature = QLabel("")
        self.lbl_signature.setStyleSheet("""
            font: 9pt 'Consolas'; background: #161b22; color: #58ff58;
            padding: 6px; border: 1px solid #30363d;
        """)
        self.lbl_signature.setWordWrap(True)
        inspector_layout.addWidget(self.lbl_signature)
        
        code_label = QLabel("CODE:")
        code_label.setStyleSheet("font: bold 9pt 'Consolas'; color: #c9d1d9; margin-top: 8px;")
        inspector_layout.addWidget(code_label)
        
        self.text_code_preview = QTextEdit()
        self.text_code_preview.setReadOnly(True)
        self.text_code_preview.setFont(QFont("Consolas", 9))
        self.text_code_preview.setMaximumHeight(200)
        self.text_code_preview.setStyleSheet("background: #0d1117; color: #58ff58; border: 1px solid #30363d;")
        inspector_layout.addWidget(self.text_code_preview)
        
        docstring_label = QLabel("DOCSTRING:")
        docstring_label.setStyleSheet("font: bold 9pt 'Consolas'; color: #c9d1d9; margin-top: 8px;")
        inspector_layout.addWidget(docstring_label)
        
        self.text_docstring = QTextEdit()
        self.text_docstring.setReadOnly(True)
        self.text_docstring.setFont(QFont("Consolas", 9))
        self.text_docstring.setMaximumHeight(80)
        self.text_docstring.setStyleSheet("background: #161b22; color: #8b949e; border: 1px solid #30363d;")
        self.text_docstring.setPlaceholderText("NO_DOCSTRING")
        inspector_layout.addWidget(self.text_docstring)
        
        stats_h = QHBoxLayout()
        self.lbl_complexity = QLabel("COMPLEXITY:-")
        self.lbl_complexity.setStyleSheet("font: 9pt 'Consolas'; color: #8b949e;")
        self.lbl_lines = QLabel("LINES:-")
        self.lbl_lines.setStyleSheet("font: 9pt 'Consolas'; color: #8b949e;")
        stats_h.addWidget(self.lbl_complexity)
        stats_h.addWidget(self.lbl_lines)
        stats_h.addStretch()
        inspector_layout.addLayout(stats_h)
        
        actions_h = QHBoxLayout()
        
        btn_create_task = QPushButton("[+] CREATE_TASK")
        btn_create_task.clicked.connect(self._on_create_task_clicked)
        btn_create_task.setStyleSheet("""
            QPushButton { background: #0d1117; color: #3fb950; border: 2px solid #3fb950;
                         padding: 8px 16px; font: bold 10pt 'Consolas'; }
            QPushButton:hover { background: #3fb950; color: #0d1117; }
        """)
        actions_h.addWidget(btn_create_task)
        
        btn_no_issue = QPushButton("[X] NO_ISSUE")
        btn_no_issue.clicked.connect(self._on_no_issue_clicked)
        btn_no_issue.setStyleSheet("""
            QPushButton { background: #0d1117; color: #8b949e; border: 2px solid #30363d;
                         padding: 8px 16px; font: bold 10pt 'Consolas'; }
            QPushButton:hover { background: #30363d; }
        """)
        actions_h.addWidget(btn_no_issue)
        
        inspector_layout.addLayout(actions_h)
        layout.addWidget(inspector_frame)
    
    def show_method(self, method):
        """Affiche méthode (COPIÉ de _show_method_in_inspector L1361-1410)."""
        self.setVisible(True)
        self.current_method = method
        
        self.lbl_method_name.setText(f"📄 {method.method_name}()")
        self.lbl_method_file.setText(f"📁 File: {method.file}")
        self.lbl_method_class.setText(f"🏷️ Class: {method.class_name}")
        self.lbl_method_line.setText(f"📍 Line: {method.lineno}")
        self.lbl_signature.setText(method.signature or "No signature")
        
        if method.code:
            lines = method.code.split('\n')[:15]
            preview = '\n'.join(lines)
            if len(method.code.split('\n')) > 15:
                preview += "\n\n... (truncated)"
            self.text_code_preview.setPlainText(preview)
        else:
            self.text_code_preview.setPlainText("No code available")
        
        if method.docstring:
            self.text_docstring.setPlainText(method.docstring)
        else:
            self.text_docstring.clear()
        
        if method.code:
            lines_count = len(method.code.split('\n'))
            self.lbl_lines.setText(f"📏 Lines: {lines_count}")
            branches = method.code.count('if ') + method.code.count('for ') + method.code.count('while ')
            complexity = "Low" if branches < 3 else ("Medium" if branches < 8 else "High")
            self.lbl_complexity.setText(f"📊 Complexity: {complexity} ({branches} branches)")
        else:
            self.lbl_lines.setText("📏 Lines: -")
            self.lbl_complexity.setText("📊 Complexity: -")
    
    def show_multi_selection(self, count: int):
        """Affiche summary (COPIÉ de _show_multi_selection_summary L1412-1424)."""
        self.setVisible(True)
        self.current_method = None
        self.lbl_method_name.setText(f"📦 {count} Methods Selected")
        self.lbl_method_file.setText("Use 'Generate Prompt' to analyze them together")
        self.lbl_method_class.setText("")
        self.lbl_method_line.setText("")
        self.lbl_signature.setText("")
        self.text_code_preview.setPlainText(f"{count} methods selected.\n\nClick 'Generate Prompt'.")
        self.lbl_complexity.setText("")
        self.lbl_lines.setText("")
    
    def _on_create_task_clicked(self):
        if self.current_method:
            self.create_task_requested.emit(self.current_method)
    
    def _on_no_issue_clicked(self):
        if self.current_method:
            self.no_issue_marked.emit(self.current_method)
