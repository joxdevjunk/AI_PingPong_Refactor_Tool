"""
Prompt Panel - Right panel pour génération/copie prompts.
Extrait de main.py _create_right_panel (L614-694).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QLineEdit, QComboBox, QCheckBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


class PromptPanel(QWidget):
    """
    Panel right: Prompt generation + Response parsing.
    Code extrait SANS modification de main.py.
    """
    
    # Signals
    generate_requested = Signal(str, str, bool)  # (template, description, code_mode)
    prompt_copied = Signal()
    response_parsed = Signal(str)  # JSON text
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI (COPIÉ de _create_right_panel L614-694)."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # === PROMPT GENERATION ===
        prompt_group = QWidget()
        prompt_layout = QVBoxLayout(prompt_group)
        
        # Controls
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Template:"))
        
        self.combo_template = QComboBox()
        self.combo_template.addItems([
            'debug_bug', 
            'feature_new', 
            'refactor_code', 
            'refactor_file'
        ])
        controls.addWidget(self.combo_template)
        
        self.check_code_mode = QCheckBox("🔥 Code")
        controls.addWidget(self.check_code_mode)
        
        prompt_layout.addLayout(controls)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Desc:"))
        
        self.input_description = QLineEdit()
        self.input_description.setPlaceholderText("Bug/feature/refactor...")
        desc_layout.addWidget(self.input_description, 1)
        
        prompt_layout.addLayout(desc_layout)
        
        # Generate button
        self.btn_generate = QPushButton("✨ Generate Prompt")
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        self.btn_generate.setEnabled(False)
        prompt_layout.addWidget(self.btn_generate)
        
        # Prompt text
        prompt_layout.addWidget(QLabel("📝 Generated Prompt"))
        
        self.text_prompt = QTextEdit()
        self.text_prompt.setReadOnly(True)
        self.text_prompt.setFont(QFont("Consolas", 9))
        prompt_layout.addWidget(self.text_prompt, 2)
        
        # Copy button
        btn_copy_prompt = QPushButton("📋 Copy Prompt")
        btn_copy_prompt.clicked.connect(self._on_copy_clicked)
        prompt_layout.addWidget(btn_copy_prompt)
        
        layout.addWidget(prompt_group, 1)
        
        # === RESPONSE ===
        response_group = QWidget()
        response_layout = QVBoxLayout(response_group)
        
        response_layout.addWidget(QLabel("💬 AI Response (JSON)"))
        
        self.text_response = QTextEdit()
        self.text_response.setFont(QFont("Consolas", 9))
        self.text_response.setPlaceholderText("Paste AI JSON here...")
        response_layout.addWidget(self.text_response, 1)
        
        btn_parse = QPushButton("🔄 Parse & Create Tasks")
        btn_parse.clicked.connect(self._on_parse_clicked)
        response_layout.addWidget(btn_parse)
        
        layout.addWidget(response_group, 1)
    
    def set_prompt(self, prompt_text: str):
        """Affiche prompt généré."""
        self.text_prompt.setPlainText(prompt_text)
    
    def get_response(self) -> str:
        """Retourne response text."""
        return self.text_response.toPlainText()
    
    def enable_generate(self, enabled: bool):
        """Active/désactive bouton generate."""
        self.btn_generate.setEnabled(enabled)
    
    def _on_generate_clicked(self):
        """Handler bouton Generate."""
        template = self.combo_template.currentText()
        description = self.input_description.text()
        code_mode = self.check_code_mode.isChecked()
        
        self.generate_requested.emit(template, description, code_mode)
    
    def _on_copy_clicked(self):
        """Handler bouton Copy (COPIÉ de copy_prompt L1694-1699)."""
        prompt = self.text_prompt.toPlainText()
        if prompt:
            QApplication.clipboard().setText(prompt)
            self.prompt_copied.emit()
    
    def _on_parse_clicked(self):
        """Handler bouton Parse."""
        response_text = self.text_response.toPlainText().strip()
        if response_text:
            self.response_parsed.emit(response_text)
