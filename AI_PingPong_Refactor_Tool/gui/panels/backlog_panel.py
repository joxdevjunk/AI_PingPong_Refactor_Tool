"""
Backlog Tab - Style BRUTALISTE LISIBLE
Bordures carrées, Consolas, badges, mais TEXTE VISIBLE
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QLineEdit, QTextEdit,
    QDialog, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QFont
from corecopy.decorators import trace_calls, detect_loops, debug_method, monitor_performance


class BacklogTab(QWidget):
    """Onglet BACKLOG - Style BRUTALISTE mais LISIBLE."""
    
    task_selected = Signal(str)
    tasks_updated = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self._task_cards = {}
        self._setup_ui()
        self._refresh_call_count = 0
    def _setup_ui(self):
        """Setup interface BRUTALISTE."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = self._create_header()
        layout.addWidget(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid #333;
                background: #0d1117;
            }
            QScrollBar:vertical {
                background: #161b22;
                width: 16px;
                border: 1px solid #30363d;
            }
            QScrollBar::handle:vertical {
                background: #8b949e;
                min-height: 40px;
                border: 1px solid #fff;
            }
            QScrollBar::handle:vertical:hover {
                background: #c9d1d9;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: #0d1117;")
        
        self.tasks_layout = QVBoxLayout(scroll_content)
        self.tasks_layout.setContentsMargins(16, 16, 16, 16)
        self.tasks_layout.setSpacing(12)
        self.tasks_layout.setAlignment(Qt.AlignTop)
        
        self.empty_label = QLabel("NO TASKS")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            color: #30363d;
            font-size: 18pt;
            font-family: 'Consolas', 'Courier New', monospace;
            font-weight: bold;
            padding: 80px;
            letter-spacing: 4px;
        """)
        self.tasks_layout.addWidget(self.empty_label)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self.scroll_content = scroll_content
    
    def _create_header(self):
        """Header BRUTALISTE."""
        header = QWidget()
        header.setStyleSheet("""
            background: #0d1117;
            border-bottom: 3px solid #ff6b6b;
            padding: 12px;
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        title = QLabel("BACKLOG")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            font-family: 'Consolas', 'Courier New', monospace;
            color: #ff6b6b;
            letter-spacing: 3px;
        """)
        layout.addWidget(title)
        
        self.stats_label = QLabel("0 tasks")
        self.stats_label.setStyleSheet("""
            color: #8b949e;
            font-family: 'Consolas', monospace;
            font-weight: bold;
        """)
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        
        self._add_filter_widgets(layout)
        
        new_btn = QPushButton("+ NEW TASK")
        new_btn.setStyleSheet("""
            QPushButton {
                background: #238636;
                color: white;
                border: 2px solid #2ea043;
                border-radius: 0px;
                padding: 8px 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: #2ea043;
                border: 2px solid #fff;
            }
        """)
        new_btn.clicked.connect(self._create_new_task)
        layout.addWidget(new_btn)
        
        return header
    
    def _add_filter_widgets(self, layout):
        """Filtres BRUTALISTES."""
        
        filter_style = """
            QComboBox {
                background: #161b22;
                color: #c9d1d9;
                border: 2px solid #30363d;
                border-radius: 0px;
                padding: 6px 12px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
            }
            QComboBox:hover {
                border: 2px solid #58a6ff;
            }
        """
        
        layout.addWidget(self._create_label("FILE:"))
        self.file_filter = QComboBox()
        self.file_filter.addItem("ALL")
        self.file_filter.setMinimumWidth(120)
        self.file_filter.setStyleSheet(filter_style)
        self.file_filter.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.file_filter)
        
        layout.addWidget(self._create_label("PRIORITY:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.priority_filter.setMinimumWidth(100)
        self.priority_filter.setStyleSheet(filter_style)
        self.priority_filter.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.priority_filter)
        
        layout.addWidget(self._create_label("CATEGORY:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("ALL")
        self.category_filter.setMinimumWidth(100)
        self.category_filter.setStyleSheet(filter_style)
        self.category_filter.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.category_filter)
        
        layout.addWidget(self._create_label("STATUS:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["ALL", "TODO", "PROGRESS", "DONE"])
        self.status_filter.setMinimumWidth(100)
        self.status_filter.setStyleSheet(filter_style)
        self.status_filter.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.status_filter)
        
        layout.addWidget(self._create_label("SORT:"))
        self.sort_order = QComboBox()
        self.sort_order.addItems([
            "Priority ↓",
            "Priority ↑",
            "File A-Z",
            "Category",
            "Date ↓"
        ])
        self.sort_order.setMinimumWidth(120)
        self.sort_order.setStyleSheet(filter_style)
        self.sort_order.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.sort_order)
    
    def _create_label(self, text):
        """Label BRUTALISTE."""
        label = QLabel(text)
        label.setStyleSheet("""
            color: #8b949e;
            font-family: 'Consolas', monospace;
            font-weight: bold;
            font-size: 9pt;
        """)
        return label

    def set_tasks(self, tasks):
        # ✅ NORMALISER UNE SEULE FOIS ici
        for task in tasks:
            if 'source_file' not in task or not task['source_file']:
                if task.get('methods') and len(task['methods']) > 0:
                    task['source_file'] = task['methods'][0].get('file', 'unknown')
                else:
                    task['source_file'] = 'manual_task'
                print(f"⚙️ Task {task.get('id', 'unknown')[:8]} normalisé → {task['source_file']}")
        
        self.tasks = tasks
        
        if hasattr(self, 'file_filter'):
            files = sorted(set(t.get('source_file', '???') for t in tasks))
            current = self.file_filter.currentText()
            
            self.file_filter.clear()
            self.file_filter.addItem("ALL")
            self.file_filter.addItems([f[:30] for f in files])
            
            idx = self.file_filter.findText(current)
            if idx >= 0:
                self.file_filter.setCurrentIndex(idx)
        
        if hasattr(self, 'category_filter'):
            cats = sorted(set(t.get('category', '???') for t in tasks if t.get('category')))
            current = self.category_filter.currentText()
            
            self.category_filter.clear()
            self.category_filter.addItem("ALL")
            self.category_filter.addItems(cats)
            
            idx = self.category_filter.findText(current)
            if idx >= 0:
                self.category_filter.setCurrentIndex(idx)
        
        self.refresh()

    def refresh(self):
        """Rafraîchit affichage."""
        """Wrapper pour tracer les appels"""
        self._refresh_call_count += 1
        print(f"\n{'='*60}")
        print(f"🔄 REFRESH #{self._refresh_call_count}")
        import traceback
        traceback.print_stack(limit=6)
        print(f"{'='*60}\n")
        #print(f"🔄 refresh() - {len(self.tasks)} tasks")
        
        try:
            if not hasattr(self, 'empty_label'):
                return
            self.empty_label.isVisible()
        except RuntimeError:
            return
        
        old_cards = self._task_cards if hasattr(self, '_task_cards') else {}
        self._task_cards = {}
        
        for task_id, card in old_cards.items():
            try:
                self.tasks_layout.removeWidget(card)
                card.deleteLater()
            except RuntimeError:
                pass
        
        old_cards.clear()
        
        if not self.tasks:
            try:
                self.empty_label.setVisible(True)
            except RuntimeError:
                pass
            self._update_stats()
            return
        
        try:
            self.empty_label.setVisible(False)
        except RuntimeError:
            pass
        
        for task in self.tasks:
            self._create_task_card(task)
        
        print(f"✅ {len(self._task_cards)} cards créées")
        
        self._apply_filters()
        self._update_stats()

    def _create_task_card(self, task):
        """Card BRUTALISTE mais 100% LISIBLE."""
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setMinimumHeight(160)  # ✅ Plus grand (140 → 160)
        card.setMaximumHeight(250)  # ✅ Plus grand (220 → 250)
        card.setProperty('task_id', task['id'])
        
        colors = {
            'critical': '#f85149',
            'high': '#ffa657',
            'medium': '#58a6ff',
            'low': '#3fb950'
        }
        border_color = colors.get(task.get('priority', 'medium'), '#58a6ff')
        
        card.setStyleSheet(f"""
            QFrame {{
                background: #0d1117;
                border: 2px solid #30363d;
                border-left: 6px solid {border_color};
                border-radius: 0px;
                padding: 16px;  /* ✅ Plus de padding (14 → 16) */
            }}
            QFrame:hover {{
                background: #161b22;
                border: 2px solid {border_color};
                border-left: 8px solid {border_color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)  # ✅ Plus de marges (12,10 → 14,12)
        layout.setSpacing(12)  # ✅ Plus d'espace vertical (10 → 12)
        
        # === HEADER ROW ===
        header_row = QHBoxLayout()
        header_row.setSpacing(12)  # ✅ Espace entre éléments
        
        # Priority badge LISIBLE
        pri_map = {'critical': 'CRITICAL', 'high': 'HIGH', 'medium': 'MEDIUM', 'low': 'LOW'}
        pri_text = pri_map.get(task.get('priority', 'medium'), 'MEDIUM')
        pri_label = QLabel(pri_text)
        pri_label.setStyleSheet(f"""
            color: {border_color};
            font-family: 'Consolas', monospace;
            font-weight: bold;
            font-size: 11pt;  /* ✅ Plus grand (10pt → 11pt) */
            background: {border_color}22;
            padding: 8px 14px;  /* ✅ Plus de padding (6,12 → 8,14) */
            border: 2px solid {border_color};
        """)
        pri_label.setFixedWidth(110)  # ✅ Plus large (100 → 110)
        pri_label.setAlignment(Qt.AlignCenter)
        header_row.addWidget(pri_label)
        
        # Title LISIBLE et COMPLET
        title_text = task.get('title', 'UNTITLED TASK')
        if not title_text or title_text.strip() == '':
            title_text = f"REFACTORING TASK {task.get('id', '???')[:8]}"
        
        # ✅ PAS DE TRONCATURE - Affiche TOUT le titre
        title_label = QLabel(title_text.upper())  # ✅ Pas de [:70]
        title_label.setStyleSheet(f"""
            color: #c9d1d9;
            font-family: 'Consolas', monospace;
            font-weight: bold;
            font-size: 12pt;  /* ✅ Taille optimale (13pt → 12pt pour plus de place) */
            letter-spacing: 0.5px;  /* ✅ Moins d'espacement (1px → 0.5px) */
            padding: 6px 10px;  /* ✅ Plus de padding (4,8 → 6,10) */
            line-height: 1.3;  /* ✅ Hauteur de ligne pour multilignes */
        """)
        title_label.setWordWrap(True)  # ✅ Retour à la ligne automatique
        header_row.addWidget(title_label, stretch=1)
        
        # Boutons
        btn_edit = QPushButton("EDIT")
        btn_edit.setFixedSize(65, 34)  # ✅ Plus grand (60,32 → 65,34)
        btn_edit.setStyleSheet("""
            QPushButton {
                background: #161b22;
                color: #58a6ff;
                border: 2px solid #30363d;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                font-size: 10pt;  /* ✅ Plus grand (9pt → 10pt) */
            }
            QPushButton:hover {
                border: 2px solid #58a6ff;
                background: #1f6feb;
                color: white;
            }
        """)
        btn_edit.clicked.connect(lambda: self._edit_task(task['id']))
        header_row.addWidget(btn_edit)
        
        btn_delete = QPushButton("DEL")
        btn_delete.setFixedSize(65, 34)  # ✅ Plus grand (60,32 → 65,34)
        btn_delete.setStyleSheet("""
            QPushButton {
                background: #161b22;
                color: #f85149;
                border: 2px solid #30363d;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                font-size: 10pt;  /* ✅ Plus grand (9pt → 10pt) */
            }
            QPushButton:hover {
                border: 2px solid #f85149;
                background: #da3633;
                color: white;
            }
        """)
        btn_delete.clicked.connect(lambda: self._delete_task(task['id']))
        header_row.addWidget(btn_delete)
        
        layout.addLayout(header_row)
        
        # === METADATA 100% LISIBLE ===
        meta = f"Effort: {task.get('effort', 'Unknown')} | Category: {task.get('category', '???').upper()}"
        if task.get('methods'):
            meta += f" | {len(task['methods'])} methods"
        
        meta_label = QLabel(meta)
        meta_label.setStyleSheet("""
            color: #8b949e;
            font-family: 'Consolas', monospace;
            font-size: 10pt;  /* ✅ Plus grand (9pt → 10pt) */
            font-weight: bold;
            padding: 4px 0px;  /* ✅ Padding vertical */
        """)
        layout.addWidget(meta_label)
        
        # === DESCRIPTION 100% LISIBLE ===
        desc = task.get('description', '')[:140]  # ✅ Plus de caractères (100 → 140)
        if len(task.get('description', '')) > 140:
            desc += "..."
        
        if desc:
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("""
                color: #c9d1d9;
                font-family: 'Consolas', monospace;
                font-size: 11pt;  /* ✅ Plus grand (10pt → 11pt) */
                line-height: 1.5;  /* ✅ Plus d'espace entre lignes (1.4 → 1.5) */
                padding: 6px 0px;  /* ✅ Padding vertical */
            """)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        # === FOOTER ===
        footer = QHBoxLayout()
        footer.setSpacing(12)
        
        # Tags 100% LISIBLES
        if task.get('tags'):
            tags = " ".join(f"#{t.upper()}" for t in task['tags'][:3])
            tags_label = QLabel(tags)
            tags_label.setStyleSheet("""
                color: #ffa657;
                font-family: 'Consolas', monospace;
                font-size: 10pt;  /* ✅ Plus grand (9pt → 10pt) */
                font-weight: bold;
                padding: 4px 0px;
            """)
            footer.addWidget(tags_label)
        
        footer.addStretch()
        
        # Status badge 100% LISIBLE
        status_map = {
            'todo': ('TODO', '#8b949e'),
            'progress': ('PROGRESS', '#ffa657'),  # ✅ Raccourci (IN PROGRESS → PROGRESS)
            'done': ('DONE', '#3fb950')
        }
        status_text, status_color = status_map.get(task.get('status', 'todo'), ('TODO', '#8b949e'))
        
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"""
            color: {status_color};
            font-family: 'Consolas', monospace;
            font-size: 11pt;  /* ✅ Plus grand (10pt → 11pt) */
            font-weight: bold;
            background: {status_color}22;
            padding: 8px 16px;  /* ✅ Plus de padding (6,14 → 8,16) */
            border: 2px solid {status_color};
        """)
        footer.addWidget(status_label)
        
        layout.addLayout(footer)
        
        card.mousePressEvent = lambda e: self._on_card_clicked(task['id'], e)
        
        self.tasks_layout.addWidget(card)
        self._task_cards[task['id']] = card

    def _on_card_clicked(self, task_id, event):
        """Handler clic."""
        if event.button() == Qt.LeftButton:
            self.task_selected.emit(task_id)
            self._edit_task(task_id)

    # ... (garde toutes les autres méthodes identiques : _edit_task, _delete_task, _create_new_task, _apply_filters, _update_stats, etc.)

    
    def _edit_task(self, task_id):
        """Dialog édition BRUTALISTE."""
        task = next((t for t in self.tasks if t.get('id') == task_id), None)
        if not task:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"[EDIT] {task['title'][:40].upper()}")
        dialog.setMinimumSize(700, 550)
        dialog.setStyleSheet("""
            QDialog {
                background: #0d1117;
                border: 3px solid #58a6ff;
            }
            QLabel {
                color: #c9d1d9;
                font-size: 10pt;
                font-family: 'Consolas', monospace;
                font-weight: bold;
            }
            QLineEdit, QTextEdit, QComboBox {
                background: #161b22;
                color: #c9d1d9;
                border: 2px solid #30363d;
                padding: 10px;
                font-family: 'Consolas', monospace;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #58a6ff;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # Title
        layout.addWidget(QLabel("[TITLE]"))
        title_edit = QLineEdit(task['title'])
        title_edit.setFont(QFont('Consolas', 11, QFont.Bold))
        layout.addWidget(title_edit)
        
        # Description
        layout.addWidget(QLabel("[DESCRIPTION]"))
        desc_edit = QTextEdit()
        desc_edit.setPlainText(task.get('description', ''))
        desc_edit.setMinimumHeight(220)
        desc_edit.setFont(QFont('Consolas', 10))
        layout.addWidget(desc_edit)
        
        # Metadata grid BRUTALISTE
        grid = QGridLayout()
        grid.setSpacing(12)
        
        grid.addWidget(QLabel("[PRIORITY]"), 0, 0)
        priority_combo = QComboBox()
        priority_combo.addItems(['low', 'medium', 'high', 'critical'])
        priority_combo.setCurrentText(task.get('priority', 'medium'))
        grid.addWidget(priority_combo, 0, 1)
        
        grid.addWidget(QLabel("[STATUS]"), 0, 2)
        status_combo = QComboBox()
        status_combo.addItems(['todo', 'progress', 'done'])
        status_combo.setCurrentText(task.get('status', 'todo'))
        grid.addWidget(status_combo, 0, 3)
        
        grid.addWidget(QLabel("[EFFORT]"), 1, 0)
        effort_edit = QLineEdit(task.get('effort', 'Unknown'))
        grid.addWidget(effort_edit, 1, 1)
        
        grid.addWidget(QLabel("[CATEGORY]"), 1, 2)
        category_edit = QLineEdit(task.get('category', 'general'))
        grid.addWidget(category_edit, 1, 3)
        
        layout.addLayout(grid)
        
        # Buttons BRUTALISTES
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("[CANCEL]")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #161b22;
                color: #8b949e;
                border: 2px solid #30363d;
                padding: 10px 24px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                border: 2px solid #8b949e;
                color: #c9d1d9;
            }
        """)
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_save = QPushButton("[SAVE]")
        btn_save.setStyleSheet("""
            QPushButton {
                background: #238636;
                color: white;
                border: 2px solid #2ea043;
                padding: 10px 24px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background: #2ea043;
                border: 2px solid #fff;
            }
            QPushButton:pressed {
                background: #1a7f37;
            }
        """)
        
        def save_changes():
            task['title'] = title_edit.text()
            task['description'] = desc_edit.toPlainText()
            task['priority'] = priority_combo.currentText()
            task['status'] = status_combo.currentText()
            task['effort'] = effort_edit.text()
            task['category'] = category_edit.text()
            
            self.refresh()
            self.tasks_updated.emit()
            dialog.accept()
        
        btn_save.clicked.connect(save_changes)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _delete_task(self, task_id):
        """Supprime task BRUTALISTE."""
        task = next((t for t in self.tasks if t.get('id') == task_id), None)
        if not task:
            return
        
        # MessageBox BRUTALISTE
        msg = QMessageBox(self)
        msg.setWindowTitle("[DELETE TASK]")
        msg.setText(f"[WARNING] DELETE TASK:\n\n'{task['title'].upper()}'\n\n[THIS CANNOT BE UNDONE]")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setStyleSheet("""
            QMessageBox {
                background: #0d1117;
                color: #c9d1d9;
                font-family: 'Consolas', monospace;
            }
            QPushButton {
                background: #161b22;
                color: #c9d1d9;
                border: 2px solid #30363d;
                padding: 8px 20px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                border: 2px solid #f85149;
            }
        """)
        
        if msg.exec() == QMessageBox.Yes:
            self.tasks.remove(task)
            self.refresh()
            self.tasks_updated.emit()
    
    def _create_new_task(self):
        """Crée nouvelle task."""
        from datetime import datetime
        
        new_task = {
            'id': f"task_{int(datetime.now().timestamp())}",
            'title': 'NEW TASK',
            'description': '',
            'priority': 'medium',
            'status': 'todo',
            'effort': 'Unknown',
            'category': 'general',
            'tags': [],
            'methods': [],
            'source': 'manual',
            'source_file': 'manual_task',  # ✅ AJOUTÉ
            'created_at': datetime.now().isoformat()
        }
        print("----",new_task)
        self.tasks.append(new_task)
        self.refresh()
        self._edit_task(new_task['id'])
        self.tasks_updated.emit()
    def _apply_filters(self):
        """Applique filtres BRUTALISTES."""
        
        print("🔍 _apply_filters() appelé")
        
        if not hasattr(self, 'tasks') or not self.tasks:
            print("❌ Pas de tasks")
            return
        
        print(f"📊 Total tasks: {len(self.tasks)}")
        print(f"📊 Total cards: {len(self._task_cards)}")
        
        # Récupérer valeurs filtres
        file_filter = self.file_filter.currentText() if hasattr(self, 'file_filter') else "ALL"
        priority_filter = self.priority_filter.currentText() if hasattr(self, 'priority_filter') else "ALL"
        category_filter = self.category_filter.currentText() if hasattr(self, 'category_filter') else "ALL"
        status_filter = self.status_filter.currentText() if hasattr(self, 'status_filter') else "ALL"
        sort_option = self.sort_order.currentText() if hasattr(self, 'sort_order') else "PRI ↓"
        
        print(f"🎯 Filtres: File={file_filter}, Pri={priority_filter}, Cat={category_filter}, Sta={status_filter}")
        
        # === FILTRAGE ===
        visible_tasks = []
        
        # Map des filtres BRUTALISTES
        priority_map = {'CRT': 'critical', 'HI': 'high', 'MID': 'medium', 'LO': 'low'}
        status_map = {'[ ]': 'todo', '[~]': 'progress', '[X]': 'done'}
        
        for task in self.tasks:
            # Test fichier
            if file_filter != "ALL":
                if task.get('source_file', '???')[:20] != file_filter:
                    continue
            
            # Test priorité
            if priority_filter != "ALL":
                task_pri = priority_map.get(priority_filter, priority_filter.lower())
                if task.get('priority', 'medium') != task_pri:
                    continue
            
            # Test catégorie
            if category_filter != "ALL":
                if task.get('category', '???') != category_filter:
                    continue
            
            # Test status
            if status_filter != "ALL":
                task_sta = status_map.get(status_filter, status_filter.lower())
                if task.get('status', 'todo') != task_sta:
                    continue
            
            visible_tasks.append(task)
        
        print(f"✅ {len(visible_tasks)}/{len(self.tasks)} tasks visibles")
        
        # === TRI ===
        priority_values = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        
        if "PRI ↓" in sort_option:
            visible_tasks.sort(key=lambda t: priority_values.get(t.get('priority', 'medium'), 0), reverse=True)
        elif "PRI ↑" in sort_option:
            visible_tasks.sort(key=lambda t: priority_values.get(t.get('priority', 'medium'), 0))
        elif "FILE A-Z" in sort_option:
            visible_tasks.sort(key=lambda t: t.get('source_file', 'zzz'))
        elif "FILE Z-A" in sort_option:
            visible_tasks.sort(key=lambda t: t.get('source_file', 'zzz'), reverse=True)
        elif "CAT" in sort_option:
            visible_tasks.sort(key=lambda t: t.get('category', 'zzz'))
        elif "DATE ↓" in sort_option:
            visible_tasks.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        elif "DATE ↑" in sort_option:
            visible_tasks.sort(key=lambda t: t.get('created_at', ''))
        
        # === AFFICHAGE ===
        print(f"🎨 Mise à jour affichage...")
        
        # Retirer toutes les cards
        for task_id, card in self._task_cards.items():
            try:
                self.tasks_layout.removeWidget(card)
                card.setVisible(False)
            except RuntimeError:
                pass
        
        # Ajouter seulement visibles
        for task in visible_tasks:
            task_id = task.get('id')
            card = self._task_cards.get(task_id)
            
            if card:
                try:
                    self.tasks_layout.addWidget(card)
                    card.setVisible(True)
                except RuntimeError:
                    pass
        
        print(f"✅ {len(visible_tasks)} cards affichées")
        
        self._update_stats_with_filter(len(visible_tasks))
    
    def _update_stats_with_filter(self, visible_count):
        """Update stats BRUTALISTE."""
        try:
            if not hasattr(self, 'stats_label'):
                return
            
            total = len(self.tasks) if hasattr(self, 'tasks') else 0
            
            if visible_count == total:
                self.stats_label.setText(f"[ {total} ]")
                self.stats_label.setStyleSheet("""
                    color: #8b949e;
                    font-family: 'Consolas', monospace;
                    font-weight: bold;
                """)
            else:
                self.stats_label.setText(f"[ {visible_count}/{total} ]")
                self.stats_label.setStyleSheet("""
                    color: #58a6ff;
                    font-family: 'Consolas', monospace;
                    font-weight: bold;
                """)
        except RuntimeError:
            pass
    
    def get_selected_tasks(self):
        """Retourne tasks."""
        return self.tasks if hasattr(self, 'tasks') else []
    
    def _update_stats(self):
        """Update stats complètes."""
        try:
            if not hasattr(self, 'stats_label'):
                return
            
            self.stats_label.isVisible()
            
            if hasattr(self, 'status_filter'):
                self.status_filter.isVisible()
        except RuntimeError:
            return
        
        if not self.tasks:
            try:
                self.stats_label.setText("[ 0 ]")
            except RuntimeError:
                pass
            return
        
        total = len(self.tasks)
        todo = sum(1 for t in self.tasks if t.get('status', 'todo') == 'todo')
        progress = sum(1 for t in self.tasks if t.get('status') == 'progress')
        done = sum(1 for t in self.tasks if t.get('status') == 'done')
        
        try:
            current_filter = self.status_filter.currentText()
        except (RuntimeError, AttributeError):
            current_filter = 'ALL'
        
        if current_filter == 'ALL':
            visible = total
        elif current_filter == '[ ]':
            visible = todo
        elif current_filter == '[~]':
            visible = progress
        else:
            visible = done
        
        stats = f"[ {visible}/{total} ] | [ ] {todo} | [~] {progress} | [X] {done}"
        
        try:
            self.stats_label.setText(stats)
        except RuntimeError:
            pass
