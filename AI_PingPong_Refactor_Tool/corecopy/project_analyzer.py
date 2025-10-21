"""
Project Analyzer V5 - Architecture 2 phases : COLLECT → BUILD
"""

import os
import sys
import ast
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict


class ProjectAnalyzer:
    """Analyse projet Python avec AST - Architecture optimisée."""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.files = []
        
        # ✅ PHASE 1: Structures temporaires de COLLECTE
        self._temp_classes = {}  # class_key → nodes & data
        self._temp_methods = defaultdict(list)  # class_key → [method_data]
        self._temp_instance_vars = defaultdict(dict)  # class_key → {method: [vars]}
        self._temp_local_vars = {}  # (class_key, method_name) → vars
        self._temp_global_functions = []
        self._temp_imports = set()
        self._temp_files_data = {}
        
        # Stats
        self.stats = {
            'total_files': 0,
            'total_lines': 0,
            'total_classes': 0,
            'total_methods': 0
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Analyse complète projet."""
        self._scan_files()
        self._collect_all_data()  # ✅ PHASE 1
        return self._build_final_json()  # ✅ PHASE 2
    
    def _scan_files(self):
        """Scan tous fichiers .py du projet."""
        for py_file in self.project_path.rglob('*.py'):
            if '__pycache__' not in str(py_file):
                self.files.append(py_file)
        self.stats['total_files'] = len(self.files)
    
    def _collect_all_data(self):
        """
        ✅ PHASE 1: COLLECTER toutes les données brutes
        """
        for file_path in self.files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                    tree = ast.parse(source, filename=str(file_path))
                    
                    # Stats
                    lines = source.count('\n') + 1
                    self.stats['total_lines'] += lines
                    
                    rel_path = str(file_path.relative_to(self.project_path))
                    self._temp_files_data[rel_path] = {
                        'lines': lines,
                        'class_keys': []
                    }
                    
                    # Imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                self._temp_imports.add(alias.name.split('.')[0])
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                self._temp_imports.add(node.module.split('.')[0])
                    
                    # Fonctions globales
                    for node in tree.body:
                        if isinstance(node, ast.FunctionDef):
                            self._temp_global_functions.append(node.name)
                    
                    # Classes
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            self._collect_class_data(node, file_path, source, rel_path)
                            
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
    
    def _collect_class_data(self, class_node: ast.ClassDef, file_path: Path, source: str, rel_path: str):
        """Collecte données d'une classe."""
        class_name = class_node.name
        class_key = f"{file_path.stem}.{class_name}"
        
        # Stocker node de classe
        self._temp_classes[class_key] = {
            'node': class_node,
            'file': rel_path,
            'source': source
        }
        
        self._temp_files_data[rel_path]['class_keys'].append(class_key)
        self.stats['total_classes'] += 1
        
        # Collecter méthodes
        source_lines = source.split('\n')
        
        for method_node in class_node.body:
            if isinstance(method_node, ast.FunctionDef):
                self._collect_method_data(class_key, method_node, source_lines)
    
    def _collect_method_data(self, class_key: str, method_node: ast.FunctionDef, source_lines: List[str]):
        """Collecte données d'une méthode."""
        method_name = method_node.name
        
        # Signature
        args = [arg.arg for arg in method_node.args.args]
        signature = f"{method_name}({', '.join(args)})"
        
        # Code
        start_line = method_node.lineno - 1
        end_line = method_node.end_lineno if hasattr(method_node, 'end_lineno') else start_line + 10
        method_code = '\n'.join(source_lines[start_line:end_line])
        
        # Variables d'instance
        instance_vars = self._find_instance_variables(method_node)
        if instance_vars:
            self._temp_instance_vars[class_key][method_name] = instance_vars
        
        # Variables locales
        local_vars = self._find_local_variables(method_node)
        self._temp_local_vars[(class_key, method_name)] = local_vars
        
        # Stocker méthode
        self._temp_methods[class_key].append({
            'name': method_name,
            'signature': signature,
            'lineno': method_node.lineno,
            'docstring': ast.get_docstring(method_node) or "",
            'code': method_code
        })
        
        self.stats['total_methods'] += 1
    
    def _find_instance_variables(self, method_node: ast.FunctionDef) -> List[str]:
        """Trouve self.xxx."""
        instance_vars = []
        
        for node in ast.walk(method_node):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                
                for target in targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name) and target.value.id == 'self':
                            var_name = target.attr
                            if var_name not in instance_vars:
                                instance_vars.append(var_name)
        
        return instance_vars
    
    def _find_local_variables(self, method_node: ast.FunctionDef) -> Dict[str, List[str]]:
        """Trouve variables locales."""
        local_vars = {
            'parameters': [],
            'assigned': [],
            'for_vars': [],
            'with_vars': []
        }
        
        # Paramètres
        for arg in method_node.args.args:
            local_vars['parameters'].append(arg.arg)
        
        if method_node.args.vararg:
            local_vars['parameters'].append(f"*{method_node.args.vararg.arg}")
        if method_node.args.kwarg:
            local_vars['parameters'].append(f"**{method_node.args.kwarg.arg}")
        
        # Corps
        for node in ast.walk(method_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    names = self._extract_names(target)
                    names = [n for n in names if not n.startswith('self.')]
                    local_vars['assigned'].extend(names)
            
            elif isinstance(node, ast.AnnAssign):
                names = self._extract_names(node.target)
                names = [n for n in names if not n.startswith('self.')]
                local_vars['assigned'].extend(names)
            
            elif isinstance(node, ast.For):
                names = self._extract_names(node.target)
                local_vars['for_vars'].extend(names)
            
            elif isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars:
                        names = self._extract_names(item.optional_vars)
                        local_vars['with_vars'].extend(names)
        
        # Dédupliquer
        for key in local_vars:
            local_vars[key] = list(dict.fromkeys(local_vars[key]))
        
        return local_vars
    
    def _extract_names(self, node: ast.AST) -> List[str]:
        """Extrait noms de variables."""
        names = []
        
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                names.extend(self._extract_names(elt))
        elif isinstance(node, ast.Attribute):
            value_names = self._extract_names(node.value)
            for v in value_names:
                names.append(f"{v}.{node.attr}")
        elif isinstance(node, ast.Subscript):
            names.extend(self._extract_names(node.value))
        
        return names
    
    def _build_final_json(self) -> Dict[str, Any]:
        """
        ✅ PHASE 2: ASSEMBLER le JSON final depuis les données collectées
        """
        final_classes = {}
        final_files_data = {}
        
        # Construire classes
        for class_key, class_data in self._temp_classes.items():
            class_node = class_data['node']
            
            # Méthodes avec local_vars intégrées
            methods = []
            for method_data in self._temp_methods[class_key]:
                method_key = (class_key, method_data['name'])
                method_data['local_vars'] = self._temp_local_vars.get(method_key, {})
                methods.append(method_data)
            
            # Classe finale
            final_classes[class_key] = {
                'file': class_data['file'],
                'name': class_node.name,
                'lineno': class_node.lineno,
                'docstring': ast.get_docstring(class_node) or "No description",
                'methods': methods,
                'num_methods': len(methods),
                'instance_variables_by_method': self._temp_instance_vars.get(class_key, {})
            }
        
        # Construire files_data
        for rel_path, data in self._temp_files_data.items():
            final_files_data[rel_path] = {
                'lines': data['lines'],
                'classes': [final_classes[k] for k in data['class_keys'] if k in final_classes]
            }
        
        return {
            'project_name': self.project_path.name,
            'project_path': str(self.project_path),
            'analyzed_at': datetime.now().isoformat(),
            'stats': self.stats,
            'classes': final_classes,
            'files': list(final_files_data.keys()),
            'files_data': final_files_data,
            'imports': sorted(list(self._temp_imports)),
            'global_functions': self._temp_global_functions
        }
