"""
Configuration globale singleton.
Extrait de main.py lignes 69-157 (_apply_dark_theme).
"""

import os
import json
from pathlib import Path
from typing import Optional


class AppConfig:
    """
    Singleton configuration manager.
    Handles theme, paths, and app settings.
    """
    
    _instance: Optional['AppConfig'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not AppConfig._initialized:
            self._init_config()
            AppConfig._initialized = True
    
    def _init_config(self):
        """Initialize configuration once."""
        # === PATHS ===
        self.project_root = os.getcwd()
        self.template_dir = "templates/prompts"
        self.data_dir = "data"
        self.tasks_filename = ".ai_pingpong_tasks.json"
        self.analysis_filename = ".ai_pingpong_analysis.json"
        
        # === UI SETTINGS ===
        self.theme = "dark"  # "dark" | "light"
        self.language = "en"
        self.window_size = (1600, 900)
        
        # === FEATURE FLAGS ===
        self.enable_debug_menu = True
        self.enable_backlog_autosave = True
        self.max_prompt_tasks = 10
        
        # Load from file if exists
        self._load_from_file()
    
    def _load_from_file(self):
        """Load config from JSON if exists."""
        config_file = Path(self.data_dir) / "config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                
                self.theme = data.get('theme', self.theme)
                self.language = data.get('language', self.language)
                self.window_size = tuple(data.get('window_size', self.window_size))
                
                print(f"✓ Loaded config from {config_file}")
            except Exception as e:
                print(f"⚠️ Could not load config: {e}")
    
    def save(self):
        """Persist config to JSON."""
        config_file = Path(self.data_dir) / "config.json"
        config_file.parent.mkdir(exist_ok=True)
        
        data = {
            'theme': self.theme,
            'language': self.language,
            'window_size': list(self.window_size)
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Config saved to {config_file}")
    
    # === THEME STYLESHEETS ===
    
    def get_main_stylesheet(self) -> str:
        """Retourne stylesheet principal window."""
        if self.theme == "dark":
            return self._dark_theme_stylesheet()
        return ""
    
    def get_dialog_stylesheet(self) -> str:
        """Retourne stylesheet pour dialogs."""
        if self.theme == "dark":
            return self._dark_dialog_stylesheet()
        return ""
    
    def _dark_theme_stylesheet(self) -> str:
        """Dark theme Matrix-style (extrait de main.py L69-157)."""
        return """
            QMainWindow, QWidget {
                background-color: #0d1117;
                color: #c9d1d9;
            }
            
            QTreeWidget {
                background-color: #161b22;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
            }
            QTreeWidget::item:selected {
                background-color: #238636;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #21262d;
            }
            
            QLabel {
                color: #c9d1d9;
            }
            
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #58a6ff;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
            
            QTextEdit {
                background-color: #0d1117;
                color: #58ff58;
                border: 1px solid #30363d;
                border-radius: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                padding: 8px;
            }
            
            QLineEdit, QComboBox {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                padding: 8px;
                border-radius: 6px;
            }
            QComboBox:hover, QLineEdit:focus {
                border-color: #58a6ff;
            }
            
            QCheckBox {
                color: #c9d1d9;
            }
            QCheckBox::indicator:checked {
                background-color: #238636;
                border: 2px solid #238636;
            }
            
            QScrollBar:vertical {
                background-color: #161b22;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #30363d;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #484f58;
            }
            
            QStatusBar {
                background-color: #161b22;
                color: #58ff58;
                border-top: 1px solid #30363d;
            }
            
            QTabWidget::pane {
                background: #0d1117;
                border: 1px solid #30363d;
            }
            QTabBar::tab {
                background: #161b22;
                color: #8b949e;
                border: 1px solid #30363d;
                padding: 10px 24px;
                margin-right: 2px;
                font: bold 10pt 'Consolas';
            }
            QTabBar::tab:selected {
                background: #0d1117;
                color: #58a6ff;
                border-bottom: 3px solid #58a6ff;
            }
            QTabBar::tab:hover {
                background: #1f2937;
                color: #c9d1d9;
            }
        """
    
    def _dark_dialog_stylesheet(self) -> str:
        """Stylesheet pour dialogs."""
        return """
            QDialog {
                background-color: #0d1117;
                color: #c9d1d9;
            }
            
            QLabel {
                color: #c9d1d9;
            }
            
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #30363d;
            }
        """


# === USAGE EXAMPLE ===
if __name__ == '__main__':
    config = AppConfig()
    print(f"Theme: {config.theme}")
    print(f"Data dir: {config.data_dir}")
    print(f"Window size: {config.window_size}")
    
    # Test stylesheet
    stylesheet = config.get_main_stylesheet()
    assert "background-color: #0d1117" in stylesheet
    print("✅ Config OK")
