"""Filter Widget - Filtres réutilisables."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLabel

class FilterWidget(QWidget):
    """Widget filtres générique."""
    
    def __init__(self, filters_config: dict, parent=None):
        super().__init__(parent)
        self.filters = {}
        self._setup_ui(filters_config)
    
    def _setup_ui(self, config):
        layout = QHBoxLayout(self)
        
        for name, options in config.items():
            layout.addWidget(QLabel(f"{name}:"))
            
            combo = QComboBox()
            combo.addItems(options)
            combo.currentTextChanged.connect(lambda t, n=name: self._on_filter_changed(n, t))
            
            self.filters[name] = combo
            layout.addWidget(combo)
        
        layout.addStretch()
    
    def _on_filter_changed(self, name, value):
        """Override in subclass."""
        pass
    
    def get_active_filters(self) -> dict:
        return {name: combo.currentText() for name, combo in self.filters.items()}
