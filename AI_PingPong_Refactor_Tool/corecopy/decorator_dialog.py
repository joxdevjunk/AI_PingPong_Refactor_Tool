"""
Dialog pour sélectionner les décorateurs à appliquer.
"""

# ✅ CORRECTION : PySide6 (pas PyQt5 ni PyQt6)
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QCheckBox, QGroupBox, QScrollArea, QWidget,
    QTextEdit, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette

from corecopy.decorator_injector import DecoratorInjector


class DecoratorSelectionDialog(QDialog):
    """Dialog pour sélectionner les décorateurs à appliquer."""
    
    def __init__(self, selected_methods: list, project_path, parent=None):
        """
        Args:
            selected_methods: Liste de dicts avec 'file', 'class_name', 'method_name'
            project_path: Chemin du projet
        """
        super().__init__(parent)
        self.selected_methods = selected_methods
        self.injector = DecoratorInjector(project_path)
        self.decorator_checkboxes = {}
        
        self.setWindowTitle("🐛 Apply Debug Decorators")
        self.setMinimumSize(700, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(
            f"<h2>🎯 Apply Decorators to {len(self.selected_methods)} method(s)</h2>"
        )
        layout.addWidget(header)
        
        # Liste des méthodes sélectionnées
        methods_group = QGroupBox("Selected Methods")
        methods_layout = QVBoxLayout()
        
        for method in self.selected_methods:
            label = QLabel(
                f"📍 <b>{method['class_name']}.{method['method_name']}</b> "
                f"<i>({method['file']})</i>"
            )
            methods_layout.addWidget(label)
        
        methods_group.setLayout(methods_layout)
        layout.addWidget(methods_group)
        
        # Sélection des décorateurs
        decorators_group = QGroupBox("🔧 Select Decorators to Apply")
        decorators_layout = QVBoxLayout()
        
        for dec_type, dec_info in DecoratorInjector.DECORATOR_TYPES.items():
            checkbox = QCheckBox(f"{dec_info['name']} - {dec_info['description']}")
            checkbox.setChecked(False)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    font-size: 13px;
                    padding: 5px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {dec_info['color']};
                }}
            """)
            
            self.decorator_checkboxes[dec_type] = checkbox
            decorators_layout.addWidget(checkbox)
        
        decorators_group.setLayout(decorators_layout)
        layout.addWidget(decorators_group)
        
        # Presets rapides
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("<b>Quick Presets:</b>"))
        
        btn_trace = QPushButton("🔍 Trace Only")
        btn_trace.clicked.connect(lambda: self._apply_preset(['trace']))
        
        btn_debug = QPushButton("🐛 Full Debug")
        btn_debug.clicked.connect(lambda: self._apply_preset(['trace', 'loop_detect']))
        
        btn_perf = QPushButton("⚡ Performance")
        btn_perf.clicked.connect(lambda: self._apply_preset(['performance']))
        
        btn_all = QPushButton("✨ All")
        btn_all.clicked.connect(lambda: self._apply_preset(list(DecoratorInjector.DECORATOR_TYPES.keys())))
        
        presets_layout.addWidget(btn_trace)
        presets_layout.addWidget(btn_debug)
        presets_layout.addWidget(btn_perf)
        presets_layout.addWidget(btn_all)
        presets_layout.addStretch()
        
        layout.addLayout(presets_layout)
        
        # Preview du code généré
        preview_group = QGroupBox("📄 Code Preview (for permanent injection)")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setStyleSheet("font-family: 'Courier New'; font-size: 11px;")
        
        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Connecter checkboxes à la preview
        for checkbox in self.decorator_checkboxes.values():
            checkbox.toggled.connect(self._update_preview)
        
        # Boutons action
        buttons_layout = QHBoxLayout()
        
        btn_apply_runtime = QPushButton("⚡ Apply at Runtime (Dynamic)")
        btn_apply_runtime.setStyleSheet("background-color: #4A90E2; color: white; padding: 10px;")
        btn_apply_runtime.clicked.connect(self._apply_runtime)
        
        btn_generate_code = QPushButton("💾 Generate Code (Permanent)")
        btn_generate_code.setStyleSheet("background-color: #9B4AE2; color: white; padding: 10px;")
        btn_generate_code.clicked.connect(self._generate_code)
        
        btn_cancel = QPushButton("❌ Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        buttons_layout.addWidget(btn_apply_runtime)
        buttons_layout.addWidget(btn_generate_code)
        buttons_layout.addWidget(btn_cancel)
        
        layout.addLayout(buttons_layout)
        
        # Initial preview
        self._update_preview()
    
    def _apply_preset(self, decorator_types):
        """Active un preset de décorateurs."""
        for dec_type, checkbox in self.decorator_checkboxes.items():
            checkbox.setChecked(dec_type in decorator_types)
    
    def _update_preview(self):
        """Met à jour la preview du code."""
        selected_decorators = self._get_selected_decorators()
        
        if not selected_decorators or not self.selected_methods:
            self.preview_text.setPlainText("# Select decorators to see preview")
            return
        
        method = self.selected_methods[0]
        preview = self.injector.generate_debug_code(
            method['file'],
            method['class_name'],
            method['method_name'],
            selected_decorators
        )
        
        self.preview_text.setPlainText(preview)
    
    def _get_selected_decorators(self):
        """Retourne la liste des décorateurs sélectionnés."""
        return [
            dec_type 
            for dec_type, checkbox in self.decorator_checkboxes.items()
            if checkbox.isChecked()
        ]
    
    def _apply_runtime(self):
        """Applique les décorateurs à runtime."""
        selected_decorators = self._get_selected_decorators()
        
        if not selected_decorators:
            QMessageBox.warning(self, "No Selection", "Please select at least one decorator!")
            return
        
        success_count = 0
        failed = []
        
        for method in self.selected_methods:
            if self.injector.inject_decorator(
                method['file'],
                method['class_name'],
                method['method_name'],
                selected_decorators
            ):
                success_count += 1
            else:
                failed.append(f"{method['class_name']}.{method['method_name']}")
        
        msg = f"✅ Applied decorators to {success_count}/{len(self.selected_methods)} method(s)"
        
        if failed:
            msg += f"\n\n❌ Failed:\n" + "\n".join(failed)
        
        QMessageBox.information(self, "Success", msg)
        self.accept()
    
    def _generate_code(self):
        """Génère le code avec décorateurs (pour injection permanente)."""
        selected_decorators = self._get_selected_decorators()
        
        if not selected_decorators:
            QMessageBox.warning(self, "No Selection", "Please select at least one decorator!")
            return
        
        generated_code = "# GENERATED DEBUG CODE\n\n"
        generated_code += "# Add these imports at the top of your file:\n"
        generated_code += "from core.decorators import trace_calls, detect_loops, debug_method, monitor_performance, count_calls\n"
        generated_code += "import logging\n\n"
        generated_code += "# Replace your methods with these decorated versions:\n\n"
        
        for method in self.selected_methods:
            code = self.injector.generate_debug_code(
                method['file'],
                method['class_name'],
                method['method_name'],
                selected_decorators
            )
            generated_code += code + "\n\n"
        
        # ✅ CORRECTION : PySide6 Dialog
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Generated Code")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(generated_code)
        text_edit.setStyleSheet("font-family: 'Courier New'; font-size: 11px;")
        layout.addWidget(text_edit)
        
        btn_copy = QPushButton("📋 Copy to Clipboard")
        btn_copy.clicked.connect(lambda: self._copy_to_clipboard(generated_code))
        layout.addWidget(btn_copy)
        
        dialog.exec()  # ✅ CORRECTION : exec() pour PySide6 (pas exec_())
    
    def _copy_to_clipboard(self, text):
        """Copie le texte dans le presse-papier."""
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", "Code copied to clipboard!")
