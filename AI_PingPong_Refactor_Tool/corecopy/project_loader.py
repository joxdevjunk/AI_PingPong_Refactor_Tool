"""
Project Loader - Auto-load tasks + Auto-analyse
Gère le cycle complet de chargement d'un projet.

Author: Perplexity AI
Date: 2025-10-19
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# Constantes
TASKS_FILENAME = '.ai_pingpong_tasks.json'
ANALYSIS_FILENAME = '.ai_pingpong_analysis.json'
BACKUP_SUFFIX = '.backup'


class ProjectLoader:
    """Gère le chargement automatique d'un projet."""
    
    def __init__(self, project_path: str):
        """
        Args:
            project_path: Chemin absolu du dossier projet
        """
        self.project_path = Path(project_path)
        self.tasks_file = self.project_path / TASKS_FILENAME
        self.analysis_file = self.project_path / ANALYSIS_FILENAME
        self.backup_file = self.project_path / (TASKS_FILENAME + BACKUP_SUFFIX)
        
        self.tasks: List[Dict] = []
        self.analysis_data: Optional[Dict] = None
    
    
    def load_project(self) -> Tuple[List[Dict], bool]:
        """
        Charge le projet complet : tasks + analyse si disponibles.
        
        Returns:
            Tuple (tasks, needs_analysis):
                - tasks: Liste des tasks chargées (peut être vide)
                - needs_analysis: True si l'analyse doit être lancée
        """
        print(f"\n📂 Loading project: {self.project_path}")
        
        # 1. Charger tasks existantes
        tasks_loaded = self._load_tasks()
        
        # 2. Vérifier si analyse existe et est récente
        analysis_loaded = self._load_analysis()
        
        # 3. Déterminer si on a besoin d'une nouvelle analyse
        needs_analysis = not analysis_loaded or self._is_analysis_outdated()
        
        if needs_analysis:
            print(f"🔄 Analysis needed")
        else:
            print(f"✅ Analysis up to date")
        
        return self.tasks, needs_analysis
    
    
    def _load_tasks(self) -> bool:
        """
        Charge les tasks depuis .ai_pingpong_tasks.json
        
        Returns:
            True si tasks chargées avec succès
        """
        if not self.tasks_file.exists():
            print(f"⚠️ No tasks file found at {self.tasks_file}")
            return False
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            # Format simple (liste) ou avec metadata (dict)
            if isinstance(tasks_data, list):
                self.tasks = tasks_data
            elif isinstance(tasks_data, dict) and 'tasks' in tasks_data:
                self.tasks = tasks_data['tasks']
            else:
                print(f"❌ Invalid tasks format in {self.tasks_file}")
                return False
            
            print(f"✅ Loaded {len(self.tasks)} tasks from file")
            return True
        
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            
            # Tenter de charger le backup
            if self.backup_file.exists():
                print(f"🔄 Attempting to load backup...")
                return self._load_tasks_from_backup()
            
            return False
        
        except Exception as e:
            print(f"❌ Error loading tasks: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    
    def _load_tasks_from_backup(self) -> bool:
        """Charge tasks depuis le backup."""
        try:
            with open(self.backup_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            if isinstance(tasks_data, list):
                self.tasks = tasks_data
            elif isinstance(tasks_data, dict) and 'tasks' in tasks_data:
                self.tasks = tasks_data['tasks']
            else:
                return False
            
            print(f"✅ Loaded {len(self.tasks)} tasks from backup")
            
            # Restaurer le fichier principal depuis le backup
            shutil.copy(self.backup_file, self.tasks_file)
            print(f"🔄 Restored {self.tasks_file} from backup")
            
            return True
        
        except Exception as e:
            print(f"❌ Error loading backup: {e}")
            return False
    
    
    def _load_analysis(self) -> bool:
        """
        Charge l'analyse précédente si disponible.
        
        Returns:
            True si analyse chargée avec succès
        """
        if not self.analysis_file.exists():
            print(f"⚠️ No analysis file found at {self.analysis_file}")
            return False
        
        try:
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                self.analysis_data = json.load(f)
            
            print(f"✅ Loaded previous analysis")
            return True
        
        except Exception as e:
            print(f"❌ Error loading analysis: {e}")
            return False
    
    
    def _is_analysis_outdated(self) -> bool:
        """
        Vérifie si l'analyse est obsolète (plus ancienne que les fichiers du projet).
        
        Returns:
            True si l'analyse doit être refaite
        """
        if not self.analysis_file.exists():
            return True
        
        try:
            analysis_mtime = self.analysis_file.stat().st_mtime
            
            # Vérifier si des fichiers .py ont été modifiés après l'analyse
            for py_file in self.project_path.rglob('*.py'):
                if py_file.stat().st_mtime > analysis_mtime:
                    print(f"📝 File modified after analysis: {py_file.name}")
                    return True
            
            return False
        
        except Exception as e:
            print(f"⚠️ Could not check analysis freshness: {e}")
            return True  # Par sécurité, re-analyser
    
    
    def save_tasks(self, tasks: List[Dict]) -> bool:
        """
        Sauvegarde les tasks dans .ai_pingpong_tasks.json avec backup.
        
        Args:
            tasks: Liste des tasks à sauvegarder
        
        Returns:
            True si sauvegarde réussie
        """
        try:
            # 1. Créer backup si fichier existe
            if self.tasks_file.exists():
                shutil.copy(self.tasks_file, self.backup_file)
                print(f"💾 Backup created: {self.backup_file}")
            
            # 2. Préparer données avec metadata
            data = {
                'version': '1.0',
                'project': self.project_path.name,
                'saved_at': datetime.now().isoformat(),
                'task_count': len(tasks),
                'tasks': tasks
            }
            
            # 3. Sauvegarder
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved {len(tasks)} tasks to {self.tasks_file}")
            return True
        
        except Exception as e:
            print(f"❌ Error saving tasks: {e}")
            import traceback
            traceback.print_exc()
            
            # Restaurer backup en cas d'erreur
            if self.backup_file.exists():
                try:
                    shutil.copy(self.backup_file, self.tasks_file)
                    print(f"🔄 Restored from backup after save error")
                except:
                    pass
            
            return False
    
    
    def save_analysis(self, analysis_data: Dict) -> bool:
        """
        Sauvegarde l'analyse dans .ai_pingpong_analysis.json
        
        Args:
            analysis_data: Données d'analyse à sauvegarder
        
        Returns:
            True si sauvegarde réussie
        """
        try:
            # Ajouter metadata
            analysis_data['analyzed_at'] = datetime.now().isoformat()
            analysis_data['project_path'] = str(self.project_path)
            
            with open(self.analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved analysis to {self.analysis_file}")
            
            self.analysis_data = analysis_data
            return True
        
        except Exception as e:
            print(f"❌ Error saving analysis: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    
    def merge_tasks(self, existing_tasks: List[Dict], new_tasks: List[Dict]) -> List[Dict]:
        """
        Merge tasks existantes avec nouvelles tasks (pas de doublons).
        
        Args:
            existing_tasks: Tasks déjà présentes
            new_tasks: Nouvelles tasks de l'analyse
        
        Returns:
            Liste mergée sans doublons
        """
        # Créer set d'IDs existants
        existing_ids = {task['id'] for task in existing_tasks}
        
        # Filtrer nouvelles tasks
        unique_new_tasks = [
            task for task in new_tasks 
            if task.get('id') not in existing_ids
        ]
        
        # Merger
        merged = existing_tasks + unique_new_tasks
        
        print(f"📊 Merge: {len(existing_tasks)} existing + {len(unique_new_tasks)} new = {len(merged)} total")
        
        return merged
    
    
    def extract_tasks_from_analysis(self, analysis_data: Dict) -> List[Dict]:
        """
        Extrait tasks depuis les données d'analyse.
        
        Args:
            analysis_data: Données brutes de l'analyse
        
        Returns:
            Liste de tasks formatées
        """
        tasks = []
        
        # Extraire depuis classes
        for class_info in analysis_data.get('classes', []):
            for method in class_info.get('methods', []):
                # ID stable basé sur file::class::method
                task_id = f"{class_info['file']}::{class_info['name']}::{method['name']}"
                
                # Extraire première ligne de docstring
                docstring = method.get('docstring', '')
                description = docstring.split('\n')[0] if docstring else ''
                
                task = {
                    'id': task_id,
                    'title': f"{class_info['name']}.{method['name']}",
                    'description': description,
                    'priority': 'medium',
                    'status': 'todo',
                    'effort': 'Unknown',
                    'category': 'refactor',
                    'tags': [],
                    'methods': [method['name']],
                    'source': 'analysis',
                    'source_file': class_info['file'],
                    'class_name': class_info['name'],
                    'created_at': datetime.now().isoformat()
                }
                
                tasks.append(task)
        
        print(f"🔍 Extracted {len(tasks)} tasks from analysis")
        
        return tasks
    
    
    def get_project_info(self) -> Dict:
        """
        Retourne informations sur le projet.
        
        Returns:
            Dict avec path, nom, stats
        """
        return {
            'path': str(self.project_path),
            'name': self.project_path.name,
            'tasks_file': str(self.tasks_file),
            'tasks_exist': self.tasks_file.exists(),
            'task_count': len(self.tasks),
            'analysis_file': str(self.analysis_file),
            'analysis_exist': self.analysis_file.exists(),
            'analysis_data': self.analysis_data
        }
