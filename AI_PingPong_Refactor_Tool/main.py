"""
AI PingPong Analyzer V3 - MVP GUI avec sélection tasks
"""

TASKS_FILENAME = '.ai_pingpong_tasks.json'
ANALYSIS_FILENAME = '.ai_pingpong_analysis.json'



import sys
import json
from typing import List, Dict, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QComboBox, 
    QCheckBox, QLineEdit, QSplitter, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QTreeWidgetItemIterator, QTabWidget, QListWidget, QListWidgetItem ,QFrame ,
    QScrollArea,QGridLayout,QDialog
)
from datetime import datetime 

from PySide6.QtCore import Qt, QItemSelectionModel 
from PySide6.QtGui import QFont,QColor

# Import core modules
from corecopy.project_analyzer import ProjectAnalyzer
from corecopy.task_manager import TaskManager
from corecopy.prompt_composer import PromptComposer
from corecopy.conversation_manager import ConversationManager


from corecopy.parsing_strategies import ResponseParser
from utils.config import AppConfig

import logging
import functools
import time
from corecopy.decorators import trace_calls, detect_loops, debug_method, monitor_performance
from corecopy.decorator_injector import DecoratorInjector
from corecopy.decorator_dialog import DecoratorSelectionDialog

# === PANEL VIEW VISION ===
from gui.panels.method_tree_panel import MethodTreePanel
from gui.panels.inspector_panel import InspectorPanel
from gui.panels.prompt_panel import PromptPanel
from gui.panels.task_board_panel import TaskBoardPanel
from gui.panels.backlog_panel import BacklogTab
# === IMPORTS DIALOGS ===
from gui.dialogs.task_edit_dialog import TaskEditDialog
from gui.dialogs.task_selection_dialog import TaskSelectionDialog
from gui.dialogs.refactoring_dialog import RefactoringDialog

class SimplePingPongGUI(QMainWindow):
    """GUI avec sélection manuelle des tasks."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI PingPong Analyzer V3 - Task Selector")
        
        # === CONFIG SINGLETON ===
        self.config = AppConfig()
        
        # Apply theme via config
        self.setStyleSheet(self.config.get_main_stylesheet())
        self.setGeometry(100, 100, *self.config.window_size)
        
        # === CORE COMPONENTS ===
        self.project_path = None
        self.analysis = None
        self.task_manager = TaskManager()
        self.composer = PromptComposer()
        self.conversation = ConversationManager()
        self.decorator_injector = DecoratorInjector(self.project_path)
        
        # === NEW: Response Parser ===
        self.response_parser = ResponseParser()

        # === Liste de task === 
        self.tasks = []
        self.next_task_id = 1
        self.selected_task = None
        # ==============================

        
        self.backlog_tab_widget = BacklogTab(self)
        self.setup_ui()
        #self._refresh_dashboard()
        self._load_tasks()
    
    def setup_ui(self):
        """Setup interface principale (SIMPLIFIÉ)."""
        self.setWindowTitle("AI PingPong Analyzer")
        self.setGeometry(100, 100, 1600, 900)
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Top controls
        main_layout.addLayout(self._create_top_controls())
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_task_selector_tab(), "📋 TASK_SELECTOR")
        self.tabs.addTab(self.backlog_tab_widget, "📌 BACKLOG")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        main_layout.addWidget(self.tabs)
        
        # Statusbar
        self.statusBar().showMessage("Ready")

    def _on_tab_changed(self, index):
        """Handler changement onglet."""
        if index == 1:  # BACKLOG tab
            self.backlog_tab_widget.refresh()

    def _create_top_controls(self):
        """Crée barre contrôles supérieure."""
        toolbar = QHBoxLayout()
        
        btn_select_project = QPushButton("📁 Select Project")
        btn_select_project.clicked.connect(self.select_project)
        toolbar.addWidget(btn_select_project)
        
        self.lbl_project = QLabel("No project selected")
        toolbar.addWidget(self.lbl_project)
        
        self.btn_analyze = QPushButton("🔍 Analyze")  # ← CHANGE: self.btn_analyze
        self.btn_analyze.clicked.connect(self.analyze_project)
        toolbar.addWidget(self.btn_analyze)
        
        toolbar.addStretch()
        return toolbar

    def _create_task_selector_tab(self):
        """Crée tab sélection tasks."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # 3 colonnes
        layout.addWidget(self._create_left_panel())     # Tree
        layout.addWidget(self._create_center_panel())   # Inspector
        layout.addWidget(self._create_right_panel())    # Prompt
        
        return tab

    def _on_backlog_changed(self):
        """Handler quand backlog modifié - sauvegarde automatique."""
        if not hasattr(self, 'tasks'):
            return
        
        # Récupérer tasks depuis backlog widget
        self.tasks = self.backlog_tab_widget.get_tasks()
        
        # Sauvegarder dans fichier
        self._save_tasks()
        
        print(f"✓ Auto-saved {len(self.tasks)} tasks after backlog change")
        
    def _on_backlog_task_selected(self, task):
        # === FIX ===
        if isinstance(task, str):
            task = next((t for t in self.tasks if t.get('id') == task), None)
            if not task:
                return
        
        print(f"Task selected: {task.get('title')}")

    def _on_backlog_tasks_updated(self):
        """Callback quand tasks modifiées."""
        self._save_tasks()

    def _on_tree_selection_changed(self, count):
        """
        Handler quand sélection tree change.
        Affiche inspector si 1 méthode cochée.
        """
        selected_tasks = self.method_tree_panel.get_selected_tasks()
        
        if len(selected_tasks) == 1:
            # Une seule méthode → Afficher dans inspector
            method = selected_tasks[0]
            self.inspector_panel.show_method(method)
        elif len(selected_tasks) == 0:
            # Aucune sélection → Cacher inspector
            self.inspector_panel.setVisible(False)
        else:
            # Multiple sélection → Summary
            self.inspector_panel.show_multi_selection(len(selected_tasks))
    def _create_left_panel(self):
        """Panneau gauche: Tree methods (DÉLÉGUÉ AU PANEL)."""
        self.method_tree_panel = MethodTreePanel()
        self.method_tree_panel.selection_changed.connect(self._on_tree_selection_changed)
        self.method_tree_panel.selection_changed.connect(self._on_method_selection_changed)
        return self.method_tree_panel
    
    def _on_method_selection_changed(self, count):
        """Handler signal du panel."""
        # Mettre à jour inspector si 1 méthode sélectionnée
        selected = self.method_tree_panel.get_selected_tasks()
        
        if len(selected) == 1:
            # Show dans inspector (si tu l'as créé)
            pass
        elif len(selected) == 0:
            # Hide inspector
            if hasattr(self, 'inspector_widget'):
                self.inspector_widget.setVisible(False)

    def _create_center_panel(self):
        """Panneau centre: Inspecteur + Tasks Board (DÉLÉGUÉ AUX PANELS)."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # === SPLITTER VERTICAL (Inspector top + Board bottom) ===
        tasks_splitter = QSplitter(Qt.Vertical)
        tasks_splitter.setHandleWidth(4)
        tasks_splitter.setStyleSheet("""
            QSplitter::handle {
                background: #30363d;
            }
            QSplitter::handle:hover {
                background: #58a6ff;
            }
        """)
        
        # === TOP: INSPECTOR PANEL ===
        self.inspector_panel = InspectorPanel()
        self.inspector_panel.create_task_requested.connect(self.create_task_from_selected_method)
        self.inspector_panel.no_issue_marked.connect(self.mark_no_issue)
        tasks_splitter.addWidget(self.inspector_panel)
        
        # === BOTTOM: TASK BOARD PANEL ===
        self.task_board_panel = TaskBoardPanel()
        self.task_board_panel.new_task_requested.connect(self._create_new_task_inline)
        self.task_board_panel.task_card_clicked.connect(self._on_task_card_clicked)
        tasks_splitter.addWidget(self.task_board_panel)
        
        # Set initial sizes (70% inspector, 30% board)
        tasks_splitter.setSizes([700, 300])
        layout.addWidget(tasks_splitter, 1)
        
        # === BACKWARD COMPATIBILITY: Refs vers labels ===
        self.lbl_high = self.task_board_panel.lbl_high
        self.lbl_medium = self.task_board_panel.lbl_medium
        self.lbl_low = self.task_board_panel.lbl_low
        self.lbl_todo = self.task_board_panel.lbl_todo
        self.lbl_progress = self.task_board_panel.lbl_progress
        self.lbl_done = self.task_board_panel.lbl_done
        self.lbl_total = self.task_board_panel.lbl_total
        self.inspector_widget = self.inspector_panel
        
        return panel

    def _create_right_panel(self):
        """Panneau droite: Prompt/Response (DÉLÉGUÉ AU PANEL)."""
        # === AVANT: 81 lignes ===
        # === APRÈS: Délégué au panel ===
        self.prompt_panel = PromptPanel()
        
        # Connect signals
        self.prompt_panel.generate_requested.connect(self._on_generate_requested)
        self.prompt_panel.response_parsed.connect(self._on_response_parsed)
        self.prompt_panel.prompt_copied.connect(
            lambda: self.statusBar().showMessage("✅ Prompt copied!")
        )
        
        return self.prompt_panel
    
    ###### METHODE #PANEL RIGHT#
    def _on_generate_requested(self, template, description, code_mode):
        """Handler génération depuis panel."""
        # Appeler generate_prompt() existante
        self.generate_prompt()

    def _on_response_parsed(self, response_text):
        """Handler parse depuis panel."""
        # Utiliser response_parser existant
        try:
            analyzed_file = self._detect_analyzed_file()
            context = {'analyzed_file': analyzed_file}
            tasks = self.response_parser.parse(response_text, context)
            
            if tasks:
                self._add_selected_tasks(tasks)
                self.statusBar().showMessage(f"✅ Parsed {len(tasks)} tasks!")
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", str(e))   

    def _add_decorators_to_selected(self):
        """Ouvre dialog pour ajouter décorateurs aux méthodes cochées."""
        # Récupérer méthodes cochées dans le tree
        if not hasattr(self, '_all_tasks'):
            QMessageBox.warning(self, "No Analysis", "Please analyze project first!")
            return
        
        selected_tasks = [task for task in self._all_tasks if task.selected]
        
        if not selected_tasks:
            QMessageBox.warning(self, "No Selection", "Please check at least one method!")
            return
        
        # Convertir en format pour dialog
        methods = []
        for task in selected_tasks:
            methods.append({
                'file': task.file,
                'class_name': task.class_name,
                'method_name': task.method_name
            })
        
        # Ouvrir dialog
        dialog = DecoratorSelectionDialog(methods, self.project_path, self)
        dialog.exec()
    
    def _remove_all_decorators(self):
        """Retire tous les décorateurs injectés."""
        count = self.decorator_injector.remove_all_decorators()
        QMessageBox.information(
            self, 
            "Decorators Removed",
            f"✅ Removed decorators from {count} method(s)"
        )
    
    def _show_instrumented_methods(self):
        """Affiche la liste des méthodes instrumentées."""
        instrumented = self.decorator_injector.get_instrumented_methods()
        
        if not instrumented:
            QMessageBox.information(
                self,
                "No Instrumentation",
                "No methods are currently instrumented."
            )
            return
        
        msg = "📋 <b>Instrumented Methods:</b><br><br>"
        
        for method_info in instrumented:
            decorators_str = ", ".join(method_info['decorators'])
            msg += (
                f"• <b>{method_info['class']}.{method_info['method']}</b><br>"
                f"  File: {method_info['file']}<br>"
                f"  Decorators: {decorators_str}<br><br>"
            )
        
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Instrumented Methods")
        dialog.setTextFormat(Qt.TextFormat.RichText)
        dialog.setText(msg)
        dialog.exec()

    def create_manual_task(self):
        """Dialog pour créer task manuellement (DÉLÉGUÉ AU DIALOG)."""
        dialog = TaskEditDialog(self)
        
        if dialog.exec() == QDialog.Accepted:
            task_data = dialog.get_task_data()
            
            if task_data:
                # Add to backlog
                self.backlog_tab.add_task(task_data)
                
                # Save
                self._save_tasks()
                
                self.statusBar().showMessage("✅ Manual task created!")

    def _refresh_dashboard(self):
        """Refresh dashboard."""
        # Clear board
        for i in reversed(range(self.board_layout.count())): 
            widget = self.board_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Stats
        high = sum(1 for t in self.tasks if t.get('priority') == 'high')
        medium = sum(1 for t in self.tasks if t.get('priority') == 'medium')
        low = sum(1 for t in self.tasks if t.get('priority') == 'low')
        
        todo = sum(1 for t in self.tasks if t.get('status') == 'todo')
        progress = sum(1 for t in self.tasks if t.get('status') == 'in_progress')
        done = sum(1 for t in self.tasks if t.get('status') == 'done')
        
        total = len(self.tasks)
        """
        # ✅ DÉLÉGUER AU BACKLOG TAB
        if hasattr(self, 'backlog_tab_widget'):
            self.backlog_tab_widget.set_tasks(self.tasks)"""
        
    def _save_task_inline(self, task):
        """Save inline edits."""
        task['_editing'] = False
        #self._refresh_dashboard()
        self._save_tasks()
        self.statusBar().showMessage(f"Task saved: {task.get('title', 'NO_TITLE')}", 3000)

    def _create_new_task_inline(self):
        """Crée une task vide éditable inline."""
        from datetime import datetime
        
        new_task = {
            'id': self.next_task_id,
            'title': '[EDIT_ME]',
            'description': 'Click to edit description...',
            'priority': 'medium',
            'status': 'todo',
            'methods': [],
            'created_at': datetime.now(),
            '_editing': True
        }
        
        self.next_task_id += 1
        self.tasks.insert(0, new_task)
        #self._refresh_dashboard()
        
        # === FIX: Sauvegarder après création ===
        self._save_tasks()
        
        self.statusBar().showMessage("New task created - click to edit", 3000)
    
    def closeEvent(self, event):
        """Handler fermeture application."""
        
        # Sauvegarder tasks avant de quitter
        if hasattr(self, 'backlog_tasks') and self.tasks:
            print("Saving tasks on exit...")
            self._save_tasks()
        
        # Accepter fermeture
        event.accept()

    def _cycle_task_status(self, task):
        """Cycle status: todo -> in_progress -> done -> todo."""
        statuses = ['todo', 'in_progress', 'done']
        current = task.get('status', 'todo')
        current_idx = statuses.index(current) if current in statuses else 0
        next_idx = (current_idx + 1) % len(statuses)
        task['status'] = statuses[next_idx]
        self._refresh_dashboard()
        self._save_tasks()

    def _cycle_task_priority(self, task):
        """Cycle priority: low -> medium -> high -> low."""
        priorities = ['low', 'medium', 'high']
        current = task.get('priority', 'medium')
        current_idx = priorities.index(current) if current in priorities else 1
        next_idx = (current_idx + 1) % len(priorities)
        task['priority'] = priorities[next_idx]
        self._refresh_dashboard()
        self._save_tasks()

    def _delete_task(self, task):
        """Supprime une task."""
        reply = QMessageBox.question(
            self,
            'DELETE_TASK',
            f"Delete task: {task.get('title', 'NO_TITLE')}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.tasks.remove(task)
            self._refresh_dashboard()
            self._save_tasks()
            self.statusBar().showMessage(f"Task deleted", 3000)

    def _edit_task(self, task):
        """Édition inline dans une zone dépliable."""
        if task.get('_editing'):
            task['_editing'] = False
            
            # === FIX: Sauvegarder quand on ferme l'édition ===
            self._save_tasks()
        else:
            for t in self.tasks:
                t['_editing'] = False
            task['_editing'] = True
        
        self._refresh_dashboard()

    def _save_tasks(self):
        """Save backlog tasks to JSON file."""
        if not self.project_path:
            return
        
        from pathlib import Path
        import json
        
        tasks_file = Path(self.project_path) / '.ai_pingpong_tasks.json'
        
        # Convert datetime to string for JSON
        tasks_data = []
        for task in self.tasks:
            task_copy = task.copy()
            
            # Convert datetime to ISO format string
            if 'created_at' in task_copy and hasattr(task_copy['created_at'], 'isoformat'):
                task_copy['created_at'] = task_copy['created_at'].isoformat()
            
            tasks_data.append(task_copy)
        
        try:
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved {len(tasks_data)} tasks to {tasks_file}")
        except Exception as e:
            print(f"✗ Error saving tasks: {e}")

    def _load_tasks(self):
        """Charge tasks depuis fichier JSON."""
        from pathlib import Path
        import json
        
        tasks_file = Path("data") / "tasks.json"
        
        # === FIX : Initialiser self.tasks AVANT tout ===
        if not hasattr(self, 'tasks'):
            self.tasks = []
        
        if not tasks_file.exists():
            print("✓ Loaded 0 tasks")
            return
        
        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tasks = data.get('tasks', [])
                
            print(f"✓ Loaded {len(self.tasks)} tasks")
            
            # Update backlog - FIX: Vérifier que widget existe ET que méthode existe
            if hasattr(self, 'backlog_tab_widget'):
                # Utiliser set_tasks (pas update_tasks)
                if hasattr(self.backlog_tab_widget, 'set_tasks'):
                    self.backlog_tab_widget.set_tasks(self.tasks)
                    self.backlog_tab_widget._apply_filters()

                elif hasattr(self.backlog_tab_widget, 'update_tasks'):
                    self.backlog_tab_widget.update_tasks(self.tasks)
            self.backlog_tab_widget.refresh()
        except Exception as e:
            print(f"✗ Error loading tasks: {e}")
            self.tasks = []

    def _on_task_card_clicked(self, task):
        """Handler quand card cliquée."""
        self.selected_task = task
        # TODO: Ouvrir dialog détails ou afficher dans panneau
        QMessageBox.information(
            self, 
            task['title'],
            f"{task['description']}\n\nMethods: {len(task.get('methods', []))}"
        )

    def _create_methods_tab(self):
        """Crée tab sélection méthodes (DÉLÉGUÉ)."""
        from gui.panels.methods_selector_panel import MethodsSelectorPanel
        
        panel = MethodsSelectorPanel(
            task_tree=self.task_tree,
            parent=self
        )
        
        # Connect signals
        panel.analyze_requested.connect(self.analyze_project)
        panel.file_summary_requested.connect(self.generate_file_summary_for_refactoring)
        panel.decorators_requested.connect(self.add_decorators_to_selected)
        
        # Stocker référence pour update stats
        self.methods_panel = panel
        
        return panel

    def _create_tasks_tab(self):
        """Dashboard visuel moderne."""
        from dashboard_view import DashboardView
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Dashboard
        self.dashboard = DashboardView()
        self.dashboard.task_clicked.connect(self._on_dashboard_task_clicked)
        layout.addWidget(self.dashboard)
        
        return tab

    def _on_dashboard_task_clicked(self, task):
        """Quand une card est cliquée."""
        # Ouvrir dialog détails
        self._show_task_detail_dialog(task)

    
    def select_project(self):
        """Sélectionne projet."""
        folder = QFileDialog.getExistingDirectory(self, "Select Python Project")
        if folder:
            self.project_path = Path(folder)
            self.lbl_project.setText(f"📁 {self.project_path.name}")
            self.lbl_project.setStyleSheet("color: #2ecc71; font-weight: bold;")
            self.btn_analyze.setEnabled(True)
            self.statusBar().showMessage(f"Project selected: {self.project_path}")
    
    def analyze_project(self):
        """Analyse projet (UTILISE PANEL)."""
        if not self.project_path:
            return
        
        self.statusBar().showMessage("Analyzing project...")
        QApplication.processEvents()
        
        try:
            analyzer = ProjectAnalyzer(str(self.project_path))
            self.analysis = analyzer.analyze()
            
            # Load tasks
            self.task_manager.load_from_analysis(self.analysis)
            self._load_tasks()
            
            # === MODIFIÉ: Populate via panel ===
            self._populate_task_tree()  # Appelle maintenant panel.populate()
            
            # === MODIFIÉ: Enable generate via panel ===
            if hasattr(self, 'prompt_panel'):
                self.prompt_panel.enable_generate(True)
            else:
                self.btn_generate.setEnabled(True)  # Fallback
            
            self.conversation.start_conversation(self.analysis['project_name'])
            self.statusBar().showMessage("✅ Analysis complete")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Analysis failed: {e}")

    def _populate_task_tree(self):
        """Remplit TreeWidget (DÉLÉGUÉ AU PANEL)."""
        # Store all tasks for selection tracking
        self._all_tasks = list(self.task_manager.get_all_tasks())
        
        # Populate panel
        self.method_tree_panel.populate(self._all_tasks)

    def on_task_selected(self, item):
        """Affiche détails de la task sélectionnée."""
        task_id = item.data(Qt.UserRole)
        
        # Find task
        self.selected_task = None
        for task in self.tasks:
            if task['id'] == task_id:
                self.selected_task = task
                break
        
        if not self.selected_task:
            return
        
        # Display details
        details = f"""# 📋 {self.selected_task['title']}

    **ID:** {self.selected_task['id']}
    **Type:** {self.selected_task['type']}
    **Priority:** {self.selected_task['priority']}
    **Status:** {self.selected_task['status']}
    **Created:** {self.selected_task['created_at'].strftime('%Y-%m-%d %H:%M')}

    ## Description

    {self.selected_task['description']}

    ## Associated Methods ({len(self.selected_task.get('methods', []))})

    """
        
        for method in self.selected_task.get('methods', []):
            details += f"- {method.get('class', '?')}.{method.get('method', '?')}()\n"
        
        self.task_detail_view.setMarkdown(details)


    def edit_selected_task(self):
        """Édite la task sélectionnée."""
        if not self.selected_task:
            QMessageBox.warning(self, "No Selection", "Select a task first!")
            return
        
        QMessageBox.information(self, "Edit", "Edit dialog coming soon!")


    def delete_selected_task(self):
        """Supprime la task sélectionnée."""
        if not self.selected_task:
            QMessageBox.warning(self, "No Selection", "Select a task first!")
            return
        
        reply = QMessageBox.question(
            self, "Delete Task",
            f"Delete task '{self.selected_task['title']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.tasks = [t for t in self.tasks if t['id'] != self.selected_task['id']]
            self.selected_task = None
            self._refresh_backlog_view()
            self.statusBar().showMessage("🗑️ Task deleted!")


    def generate_prompt_from_task(self):
        """Génère prompt depuis une task du backlog."""
        if not self.selected_task:
            QMessageBox.warning(self, "No Selection", "Select a task first!")
            return
        
        QMessageBox.information(self, "Generate", "Prompt generation from task coming soon!")


    

    
    def on_task_selection_changed(self, item, column):
        """Update inspector when method checked/clicked."""
        # Count selected
        if not hasattr(self, '_all_tasks'):
            return
        
        # Get all checked items
        iterator = QTreeWidgetItemIterator(self.task_tree, QTreeWidgetItemIterator.Checked)
        count = 0
        last_checked_item = None
        
        while iterator.value():
            item = iterator.value()
            if item.data(0, Qt.UserRole) is not None:
                count += 1
                last_checked_item = item
            iterator += 1
        
        self.lbl_selection.setText(f"{count} method(s) selected")
        
        # Update selection state
        for task in self._all_tasks:
            task.selected = False
        
        iterator = QTreeWidgetItemIterator(self.task_tree, QTreeWidgetItemIterator.Checked)
        while iterator.value():
            item = iterator.value()
            task_id = item.data(0, Qt.UserRole)
            if task_id is not None and task_id < len(self._all_tasks):
                self._all_tasks[task_id].selected = True
            iterator += 1
        
        # === SHOW IN INSPECTOR if exactly 1 selected ===
        if count == 1 and last_checked_item:
            task_id = last_checked_item.data(0, Qt.UserRole)
            if task_id is not None and task_id < len(self._all_tasks):
                self._show_method_in_inspector(self._all_tasks[task_id])
        elif count == 0:
            self.inspector_widget.setVisible(False)
        else:
            # Multiple selected: show summary
            self._show_multi_selection_summary(count)

    def _show_method_in_inspector(self, method):
        """Affiche méthode dans l'inspecteur (DÉLÉGUÉ AU PANEL)."""
        self.current_inspected_method = method
        self.inspector_panel.show_method(method)

    def _show_multi_selection_summary(self, count):
        """Show summary (DÉLÉGUÉ AU PANEL)."""
        self.inspector_panel.show_multi_selection(count)

    def create_task_from_selected_method(self):
        """Crée task depuis méthode inspectée."""
        if not hasattr(self, 'current_inspected_method') or not self.current_inspected_method:
            QMessageBox.warning(self, "No Method", "Select a method first!")
            return
        
        method = self.current_inspected_method
        
        # Quick create task
        task = {
            'id': self.next_task_id,
            'title': f"Review {method.method_name}()",
            'description': f"Analyze method in {method.class_name}",
            'type': 'bug',
            'priority': 'medium',
            'status': 'todo',
            'selected': False,  # Par défaut non sélectionnée
            'methods': [{
                'class': method.class_name,
                'method': method.method_name,
                'file': method.file,
                'line': method.lineno
            }],
            'created_at': datetime.now()
        }
        
        self.tasks.append(task)
        self.next_task_id += 1
        
        # === SAVE + REFRESH BACKLOG UNIQUEMENT (PAS dashboard) ===
        self._save_tasks()
        
        # Update BACKLOG tab only
        if hasattr(self, 'backlog_tab_widget'):
            self.backlog_tab_widget.set_tasks(self.tasks)
            self.backlog_tab_widget._apply_filters()
            self.backlog_tab_widget.refresh()

        
        # Switch to BACKLOG tab
        self.tabs.setCurrentIndex(1)
        
        self.statusBar().showMessage(f"✅ Task created! Check BACKLOG tab to select it for prompt generation!")

    def mark_no_issue(self):
        """Marque méthode comme 'pas de problème' et passe à la suivante."""
        if hasattr(self, 'current_inspected_method') and self.current_inspected_method:
            # Uncheck current
            iterator = QTreeWidgetItemIterator(self.task_tree, QTreeWidgetItemIterator.Checked)
            while iterator.value():
                item = iterator.value()
                task_id = item.data(0, Qt.UserRole)
                if task_id is not None and task_id < len(self._all_tasks):
                    if self._all_tasks[task_id] == self.current_inspected_method:
                        item.setCheckState(0, Qt.Unchecked)
                        break
                iterator += 1
            
            self.statusBar().showMessage(f"✅ {self.current_inspected_method.method_name}() marked as OK")

    def generate_prompt(self):
        """Génère prompt (DÉLÉGUÉ à PromptGenerator)."""
        from corecopy.prompt_generator import PromptGenerator
        
        if not self.analysis:
            QMessageBox.warning(self, "No Analysis", "Please analyze project first!")
            return
        
        # ✅ MODIFIÉ: Get template via prompt_panel
        template = self.prompt_panel.combo_template.currentText()
        
        # Init generator
        generator = PromptGenerator(self.composer, self.analysis)
        
        try:
            # === MODE REFACTOR_FILE ===
            if template == 'refactor_file':
                selected_tasks = [task for task in self._all_tasks if task.selected]
                
                if not selected_tasks:
                    QMessageBox.warning(self, "No Selection",
                        "Pour refactor_file:\n\n"
                        "1. Cochez UNE OU PLUSIEURS méthodes du même fichier\n"
                        "2. Le système analysera TOUTES les méthodes de ce fichier")
                    return
                
                target_file = selected_tasks[0].file
                files = set(task.file for task in selected_tasks)
                
                if len(files) > 1:
                    QMessageBox.warning(self, "Multiple Files",
                        f"⚠️ {len(files)} fichiers différents sélectionnés.\n\n"
                        "Pour refactor_file, cochez un seul fichier.")
                    return
                
                file_methods = [task for task in self._all_tasks if task.file == target_file]
                prompt = generator.generate_refactor_file(target_file, file_methods)
                
                # ✅ MODIFIÉ: Via panel
                self.prompt_panel.set_prompt(prompt)
                
                self.statusBar().showMessage(
                    f"✅ File summary generated: {len(file_methods)} methods from {target_file}"
                )
                return
            
            # === MODE NORMAL ===
            current_tab_index = self.tabs.currentIndex()
            
            if current_tab_index == 0:  # TASK_SELECTOR
                selected_tasks_dicts = self._get_selected_from_tree()
                source_info = f"from TASK_SELECTOR tree ({len(selected_tasks_dicts)} methods)"
            else:  # BACKLOG
                selected_tasks_dicts = self._get_selected_from_backlog()
                source_info = f"from BACKLOG ({len(selected_tasks_dicts)} tasks)"
            
            if not selected_tasks_dicts:
                QMessageBox.warning(self, "No Selection", "Check at least one task!")
                return
            
            # Validation
            if len(selected_tasks_dicts) > 10:
                reply = QMessageBox.question(
                    self, "Large Selection",
                    f"⚠️ {len(selected_tasks_dicts)} tasks selected.\n\n"
                    f"Recommended: 3-5 tasks max.\n\nContinue anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # ✅ MODIFIÉ: Get via panel
            description = self.prompt_panel.input_description.text()
            code_mode = self.prompt_panel.check_code_mode.isChecked()
            
            # Generate
            prompt = generator.generate_normal(template, selected_tasks_dicts, description, code_mode)
            
            # ✅ MODIFIÉ: Via panel
            self.prompt_panel.set_prompt(prompt)
            
            self.statusBar().showMessage(
                f"✅ Prompt generated {source_info} - Mode: {'CODE' if code_mode else 'ANALYSE'}"
            )
            
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Error", 
                f"Failed to generate prompt:\n\n{e}\n\n{traceback.format_exc()}")

    def _get_selected_from_tree(self) -> List[Dict]:
        """Extrait tasks cochées depuis tree."""
        selected_tasks = [task for task in self._all_tasks if task.selected]
        
        selected_tasks_dicts = []
        for task in selected_tasks:
            class_key = f"{Path(task.file).stem}.{task.class_name}"
            class_data = self.analysis['classes'].get(class_key, {})
            
            method_data = None
            for m in class_data.get('methods', []):
                if m['name'] == task.method_name:
                    method_data = m
                    break
            
            selected_tasks_dicts.append({
                'file': task.file,
                'class_name': task.class_name,
                'method_name': task.method_name,
                'lineno': task.lineno,
                'signature': task.signature,
                'code': task.code,
                'docstring': task.docstring,
                'local_vars': method_data.get('local_vars', {}) if method_data else {},
                'instance_variables_by_method': class_data.get('instance_variables_by_method', {})
            })
        
        return selected_tasks_dicts
    
    def _get_selected_from_backlog(self) -> List[Dict]:
        """Extrait tasks depuis backlog."""
        backlog_selected = self.backlog_tab_widget.get_selected_tasks()
        
        selected_tasks_dicts = []
        for task in backlog_selected:
            methods = task.get('methods', [])
            if methods:
                method = methods[0]
                selected_tasks_dicts.append({
                    'file': method.get('file', 'unknown'),
                    'class_name': method.get('class', 'UnknownClass'),
                    'method_name': method.get('method', 'unknown_method'),
                    'lineno': method.get('line', 0),
                    'signature': f"{method.get('method', 'unknown')}()",
                    'code': task.get('description', '# No code available'),
                    'docstring': task.get('title', 'No description')
                })
        
        return selected_tasks_dicts
    
    def copy_prompt(self):
        """Copie prompt dans clipboard."""
        prompt = self.text_prompt.toPlainText()
        if prompt:
            QApplication.clipboard().setText(prompt)
            self.statusBar().showMessage("✅ Prompt copied to clipboard!")
    
    def parse_response(self):
        """Parse réponse IA (DÉLÉGUÉ)."""
        response_text = self.prompt_panel.text_response.toPlainText().strip()
        
        if not response_text:
            QMessageBox.warning(self, "Empty Response", "No response to parse!")
            return
        
        try:
            analyzed_file = getattr(self, 'current_analyzed_file', 'unknown.py')
            context = {'analyzed_file': analyzed_file}
            
            tasks = self.response_parser.parse(response_text, context)
            
            if tasks:
                self._show_tasks_dialog(tasks)
            else:
                QMessageBox.information(self, "No Tasks", "No tasks found in response")
        
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Parse Error", 
                f"Failed to parse:\n\n{e}\n\n{traceback.format_exc()}")

    def _detect_analyzed_file(self):
        """Détecte le fichier source depuis les méthodes cochées.
        
        Returns:
            str: Nom du fichier analysé ou 'unknown.py' si pas de sélection
        """
        # Méthode 1 : Depuis les tasks cochées dans le tree
        if hasattr(self, '_all_tasks'):
            selected_tasks = [task for task in self._all_tasks if task.selected]
            if selected_tasks:
                # Prendre le fichier de la première task cochée
                return selected_tasks[0].file
        
        # Méthode 2 : Depuis le backlog si onglet BACKLOG actif
        if hasattr(self, 'tabs') and self.tabs.currentIndex() == 1:
            if hasattr(self, 'backlog_tab_widget'):
                backlog_tasks = self.backlog_tab_widget.get_selected_tasks()
                if backlog_tasks:
                    # Récupérer fichier de la première task backlog
                    methods = backlog_tasks[0].get('methods', [])
                    if methods:
                        return methods[0].get('file', 'unknown.py')
        
        # Méthode 3 : Fallback sur current_analyzed_file si existe
        if hasattr(self, 'current_analyzed_file'):
            return self.current_analyzed_file
        
        # Défaut
        return 'unknown.py'

    def _parse_refactoring_response(self, response, source_file='unknown.py'):
        """Parse refactoring (DÉLÉGUÉ à ResponseParser Strategy)."""
        # Appel strategy existante
        context = {'analyzed_file': source_file}
        return self.response_parser.parse(json.dumps(response), context)

    def _show_refactoring_tasks_dialog(self, tasks):
        """Affiche dialog avec tasks refactoring (DÉLÉGUÉ AU DIALOG)."""
        dialog = RefactoringDialog(self, tasks)
        
        if dialog.exec() == QDialog.Accepted:
            selected_tasks = dialog.get_selected_tasks()
            
            if selected_tasks:
                self._add_selected_tasks(selected_tasks)
                self.statusBar().showMessage(f"✅ Added {len(selected_tasks)} refactoring tasks!")

    def _show_tasks_dialog(self, ai_tasks):
        """Affiche dialog avec tasks parsées (DÉLÉGUÉ AU DIALOG)."""
        dialog = TaskSelectionDialog(self, ai_tasks)
        
        if dialog.exec() == QDialog.Accepted:
            selected_tasks = dialog.get_selected_tasks()
            
            if selected_tasks:
                self._add_selected_tasks_simple(selected_tasks)
                self.statusBar().showMessage(f"✅ Added {len(selected_tasks)} task(s)!")

    def _add_selected_tasks(self, tasks):
        """Ajoute tasks au backlog (DÉLÉGUÉ)."""
        analyzed_file = getattr(self, 'current_analyzed_file', 'unknown.py')
        
        added_count = self.task_manager.add_tasks(tasks, source_file=analyzed_file)
        
        if added_count > 0:
            # Synchroniser main.py tasks avec TaskManager
            self.tasks = self.task_manager.tasks
            
            self._save_tasks()
            self.backlog_tab_widget.set_tasks(self.tasks)
            self.statusBar().showMessage(f"✅ Added {added_count} task(s)!")
        
        return added_count

    def _refresh_backlog_view(self):
        pass
    def generate_file_summary_for_refactoring(self):
        """Génère sommaire fichier pour refactoring  VALIDATION UI.
        Elle est appelée quand:

        L'utilisateur sélectionne un fichier entier dans le tree (pas juste une méthode)

        Il veut un refactoring complet du fichier avec toutes ses méthodes

        Template Jinja2 refactor_file.jinja2 nécessite structure complète
        """
        from corecopy.prompt_generator import PromptGenerator
        
        if not self.analysis:
            QMessageBox.warning(self, "No Analysis", "Analyze project first!")
            return
        
        # Validation: doit être dans TASK_SELECTOR
        if self.tabs.currentIndex() != 0:
            QMessageBox.information(self, "Wrong Tab", 
                "File summary only works in TASK_SELECTOR tab.")
            return
        
        # Validation: doit sélectionner un FILE node
        selected_items = self.task_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Select a FILE node!")
            return
        
        selected_item = selected_items[0]
        if selected_item.data(0, Qt.UserRole + 1) != 'file':
            QMessageBox.warning(self, "Wrong Selection", 
                "Select a FILE node, not class or method!")
            return
        
        # Get file path et méthodes
        file_path = selected_item.text(0)
        file_methods = [task for task in self._all_tasks if task.file == file_path]
        
        if not file_methods:
            QMessageBox.warning(self, "No Methods", f"No methods in {file_path}")
            return
        
        # ✅ DÉLÉGUER génération à PromptGenerator
        try:
            generator = PromptGenerator(self.composer, self.analysis)
            prompt = generator.generate_refactor_file(file_path, file_methods)
            
            # Afficher prompt
            self.prompt_panel.set_prompt(prompt)
            self.statusBar().showMessage(
                f"✅ File summary: {len(file_methods)} methods from {file_path}"
            )
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Error", 
                f"Failed:\n\n{e}\n\n{traceback.format_exc()}")

    def _build_file_summary_data(self, file_path, file_data):
        """Build file summary (DÉLÉGUÉ à FileAnalyzer)."""
        from corecopy.file_analyzer import FileAnalyzer
        return FileAnalyzer.build_summary(file_path, file_data)


    def _extract_params_from_signature(self, signature: str) -> list[str]:
        """Extract params (DÉLÉGUÉ)."""
        from utils.code_helpers import CodeHelpers
        return CodeHelpers.extract_params_from_signature(signature)

    def _clean_param(self, param):
        """Clean single parameter name."""
        param = param.strip()
        if not param:
            return None
        
        # Keep *args and **kwargs as-is
        if param.startswith('**') or param.startswith('*'):
            if '=' in param:
                param = param.split('=')[0].strip()
            if ':' in param:
                param = param.split(':')[0].strip()
            return param
        
        # Remove default value
        if '=' in param:
            param = param.split('=')[0].strip()
        
        # Remove type hint
        if ':' in param:
            param = param.split(':')[0].strip()
        
        return param if param else None


    def _detect_signals_in_code(self, code):
        """Detect Qt signals emitted in method code."""
        import re
        
        if not code:
            return []
        
        pattern = r'self\.(\w+)\.emit\s*\('
        matches = re.findall(pattern, code)
        
        return sorted(set(matches))

    def parse_ai_refactoring_response(self, json_data):
        """Parse AI refactoring (DÉLÉGUÉ à ResponseParser Strategy)."""
        # Appel strategy existante
        analyzed_file = getattr(self, 'current_analyzed_file', 'unknown.py')
        context = {'analyzed_file': analyzed_file}
        
        if isinstance(json_data, str):
            return self.response_parser.parse(json_data, context)
        else:
            return self.response_parser.parse(json.dumps(json_data), context)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = SimplePingPongGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
