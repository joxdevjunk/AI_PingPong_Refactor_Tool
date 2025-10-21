"""
Task Manager - Gestion des sélections de code
"""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Task:
    """Représente une tâche (méthode/classe) sélectionnable."""
    task_id: str  # file.py:ClassName.method_name
    file: str
    class_name: str
    method_name: str
    lineno: int
    code: str
    docstring: str
    signature: str
    is_selected: bool = False
    lines_count: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        return cls(**data)


class TaskManager:
    """Gère les tâches et sélections."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.selections_dir = Path('data/selections')
        self.selections_dir.mkdir(parents=True, exist_ok=True)
    
    def load_from_analysis(self, analysis: Dict):
        """Charge tasks depuis analyse projet."""
        self.tasks.clear()
        
        for class_key, class_info in analysis.get('classes', {}).items():
            file = class_info['file']
            class_name = class_info['name']
            
            for method in class_info.get('methods', []):
                task_id = f"{file}:{class_name}.{method['name']}"
                
                task = Task(
                    task_id=task_id,
                    file=file,
                    class_name=class_name,
                    method_name=method['name'],
                    lineno=method['lineno'],
                    code=method.get('code', ''),  # Will be loaded on demand
                    docstring=method.get('docstring', ''),
                    signature=method.get('signature', f"{method['name']}(...)"),
                    lines_count=0
                )
                self.tasks[task_id] = task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Récupère une task par ID."""
        return self.tasks.get(task_id)
    
    def select_task(self, task_id: str, selected: bool = True):
        """Sélectionne/désélectionne une task."""
        if task_id in self.tasks:
            self.tasks[task_id].is_selected = selected
    
    def select_all(self):
        """Sélectionne toutes les tasks."""
        for task in self.tasks.values():
            task.is_selected = True
    
    def clear_selection(self):
        """Désélectionne toutes les tasks."""
        for task in self.tasks.values():
            task.is_selected = False
    
    def get_selected_tasks(self) -> List[Task]:
        """Retourne tasks sélectionnées."""
        return [task for task in self.tasks.values() if task.is_selected]
    
    def add_tasks(self, tasks: list, source_file: str = 'unknown.py') -> int:
        """Ajoute multiple tasks avec normalisation."""
        from datetime import datetime
        
        # ✅ FIX: Vérifier que self.tasks est une liste de dicts
        if not isinstance(self.tasks, list):
            self.tasks = []
        
        # ✅ FIX: Nettoyer self.tasks des strings
        self.tasks = [t for t in self.tasks if isinstance(t, dict)]
        
        added_count = 0
        
        for task_data in tasks:
            try:
                # Vérifier que c'est un dict
                if not isinstance(task_data, dict):
                    continue
                
                # Détection format
                is_old_format = 'methods' in task_data
                
                if is_old_format:
                    task = {
                        'id': task_data.get('id', f"task_{datetime.now().timestamp()}"),
                        'title': task_data.get('title', 'Untitled Task'),
                        'description': task_data.get('description', ''),
                        'priority': task_data.get('priority', 'medium'),
                        'status': task_data.get('status', 'todo'),
                        'category': task_data.get('category', 'general'),
                        'effort': task_data.get('effort', 'Unknown'),
                        'tags': task_data.get('tags', []),
                        'created_at': task_data.get('created_at', datetime.now().isoformat()),
                        'methods': task_data.get('methods', []),
                        'source': task_data.get('source', 'ai_task'),
                        'source_file': task_data.get('source_file', source_file)
                    }
                else:
                    task = {
                        'id': task_data.get('id', f"task_{datetime.now().timestamp()}"),
                        'title': task_data['title'],
                        'description': task_data['description'],
                        'priority': task_data.get('priority', 'medium'),
                        'status': 'todo',
                        'category': task_data.get('category', 'refactoring'),
                        'effort': task_data.get('effort', 'Unknown'),
                        'tags': task_data.get('tags', []),
                        'created_at': datetime.now().isoformat(),
                        'methods': [],
                        'source': 'ai_refactoring',
                        'source_file': task_data.get('source_file', source_file)
                    }
                
                # ✅ FIX: Éviter doublons (safe)
                task_id = task.get('id')
                if not any(t.get('id') == task_id for t in self.tasks if isinstance(t, dict)):
                    self.tasks.append(task)
                    added_count += 1
            
            except Exception as e:
                import traceback
                print(f"Failed to add task: {e}")
                traceback.print_exc()
        
        return added_count


    def get_all_tasks(self) -> List[Task]:
        """Retourne toutes les tasks."""
        return list(self.tasks.values())
    
    def filter_tasks(self, 
                     file_pattern: str = None,
                     class_pattern: str = None,
                     min_lines: int = None) -> List[Task]:
        """Filtre tasks selon critères."""
        filtered = self.get_all_tasks()
        
        if file_pattern:
            filtered = [t for t in filtered if file_pattern.lower() in t.file.lower()]
        
        if class_pattern:
            filtered = [t for t in filtered if class_pattern.lower() in t.class_name.lower()]
        
        if min_lines:
            filtered = [t for t in filtered if t.lines_count >= min_lines]
        
        return filtered
    
    def save_selection(self, name: str) -> str:
        """Sauvegarde sélection courante."""
        selected = self.get_selected_tasks()
        selection_data = {
            'name': name,
            'timestamp': str(Path.cwd()),
            'tasks': [task.to_dict() for task in selected]
        }
        
        filepath = self.selections_dir / f"{name}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(selection_data, f, indent=2)
        
        return str(filepath)
    
    def load_selection(self, name: str):
        """Charge une sélection sauvegardée."""
        filepath = self.selections_dir / f"{name}.json"
        
        if not filepath.exists():
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            selection_data = json.load(f)
        
        # Clear current selection
        self.clear_selection()
        
        # Restore selection
        for task_data in selection_data.get('tasks', []):
            task_id = task_data['task_id']
            if task_id in self.tasks:
                self.tasks[task_id].is_selected = True
        
        return True
    
    def list_saved_selections(self) -> List[str]:
        """Liste les sélections sauvegardées."""
        return [f.stem for f in self.selections_dir.glob('*.json')]
    
    def get_stats(self) -> Dict:
        """Stats sur tasks."""
        selected = self.get_selected_tasks()
        return {
            'total_tasks': len(self.tasks),
            'selected_tasks': len(selected),
            'total_files': len(set(t.file for t in self.tasks.values())),
            'selected_files': len(set(t.file for t in selected))
        }
