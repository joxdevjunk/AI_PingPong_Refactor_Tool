"""
Code Injector - Injection intelligente de code dans projet
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import difflib


class CodeInjector:
    """Injecte code généré dans fichiers projet."""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.backup_dir = self.project_path / '.ai_backups'
        self.backup_dir.mkdir(exist_ok=True)
    
    def inject_code(self, 
                   filename: str,
                   code: str,
                   mode: str = 'replace',  # replace, append, insert_after, insert_before
                   marker: str = None) -> Dict:
        """Injecte code dans fichier."""
        
        filepath = self.project_path / filename
        
        # Backup original
        backup_path = self._backup_file(filepath)
        
        try:
            if mode == 'create':
                return self._create_file(filepath, code)
            elif mode == 'replace':
                return self._replace_file(filepath, code)
            elif mode == 'append':
                return self._append_to_file(filepath, code)
            elif mode == 'insert_after':
                return self._insert_after_marker(filepath, code, marker)
            elif mode == 'insert_before':
                return self._insert_before_marker(filepath, code, marker)
            elif mode == 'replace_method':
                return self._replace_method(filepath, code, marker)
            else:
                return {'success': False, 'error': f'Unknown mode: {mode}'}
                
        except Exception as e:
            # Restore backup on error
            self._restore_backup(filepath, backup_path)
            return {'success': False, 'error': str(e), 'restored': True}
    
    def _create_file(self, filepath: Path, code: str) -> Dict:
        """Crée nouveau fichier."""
        if filepath.exists():
            return {'success': False, 'error': 'File already exists'}
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return {
            'success': True,
            'mode': 'create',
            'file': str(filepath),
            'lines_added': code.count('\n') + 1
        }
    
    def _replace_file(self, filepath: Path, code: str) -> Dict:
        """Remplace contenu complet."""
        if not filepath.exists():
            return self._create_file(filepath, code)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            old_code = f.read()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Generate diff
        diff = self._generate_diff(old_code, code, str(filepath))
        
        return {
            'success': True,
            'mode': 'replace',
            'file': str(filepath),
            'lines_added': code.count('\n') + 1,
            'lines_removed': old_code.count('\n') + 1,
            'diff': diff
        }
    
    def _append_to_file(self, filepath: Path, code: str) -> Dict:
        """Ajoute code à la fin."""
        if not filepath.exists():
            return self._create_file(filepath, code)
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write('\n\n' + code)
        
        return {
            'success': True,
            'mode': 'append',
            'file': str(filepath),
            'lines_added': code.count('\n') + 1
        }
    
    def _insert_after_marker(self, filepath: Path, code: str, marker: str) -> Dict:
        """Insère code après marker (classe, méthode, ligne spécifique)."""
        if not filepath.exists():
            return {'success': False, 'error': 'File does not exist'}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find marker
        insert_line = None
        for i, line in enumerate(lines):
            if marker in line:
                insert_line = i + 1
                break
        
        if insert_line is None:
            return {'success': False, 'error': f'Marker not found: {marker}'}
        
        # Insert code
        code_lines = code.split('\n')
        for line in reversed(code_lines):
            lines.insert(insert_line, line + '\n')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return {
            'success': True,
            'mode': 'insert_after',
            'file': str(filepath),
            'marker': marker,
            'insert_line': insert_line,
            'lines_added': len(code_lines)
        }
    
    def _insert_before_marker(self, filepath: Path, code: str, marker: str) -> Dict:
        """Insère code avant marker."""
        if not filepath.exists():
            return {'success': False, 'error': 'File does not exist'}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find marker
        insert_line = None
        for i, line in enumerate(lines):
            if marker in line:
                insert_line = i
                break
        
        if insert_line is None:
            return {'success': False, 'error': f'Marker not found: {marker}'}
        
        # Insert code
        code_lines = code.split('\n')
        for line in reversed(code_lines):
            lines.insert(insert_line, line + '\n')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return {
            'success': True,
            'mode': 'insert_before',
            'file': str(filepath),
            'marker': marker,
            'insert_line': insert_line,
            'lines_added': len(code_lines)
        }
    
    def _replace_method(self, filepath: Path, code: str, method_name: str) -> Dict:
        """Remplace une méthode existante."""
        if not filepath.exists():
            return {'success': False, 'error': 'File does not exist'}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return {'success': False, 'error': 'File contains syntax errors'}
        
        # Find method
        method_found = False
        start_line = None
        end_line = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == method_name:
                method_found = True
                start_line = node.lineno - 1
                end_line = node.end_lineno
                break
        
        if not method_found:
            return {'success': False, 'error': f'Method not found: {method_name}'}
        
        # Replace method
        lines = content.split('\n')
        new_lines = lines[:start_line] + code.split('\n') + lines[end_line:]
        new_content = '\n'.join(new_lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        diff = self._generate_diff(content, new_content, str(filepath))
        
        return {
            'success': True,
            'mode': 'replace_method',
            'file': str(filepath),
            'method': method_name,
            'start_line': start_line + 1,
            'end_line': end_line,
            'diff': diff
        }
    
    def _backup_file(self, filepath: Path) -> Path:
        """Crée backup."""
        if not filepath.exists():
            return None
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
        backup_path = self.backup_dir / backup_name
        
        import shutil
        shutil.copy2(filepath, backup_path)
        
        return backup_path
    
    def _restore_backup(self, filepath: Path, backup_path: Path):
        """Restaure backup."""
        if backup_path and backup_path.exists():
            import shutil
            shutil.copy2(backup_path, filepath)
    
    def _generate_diff(self, old: str, new: str, filename: str) -> str:
        """Génère diff lisible."""
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f'{filename} (before)',
            tofile=f'{filename} (after)',
            lineterm=''
        )
        
        return ''.join(diff)
    
    def preview_injection(self, 
                         filename: str,
                         code: str,
                         mode: str,
                         marker: str = None) -> Dict:
        """Preview injection sans écrire."""
        filepath = self.project_path / filename
        
        if not filepath.exists() and mode != 'create':
            return {'success': False, 'error': 'File does not exist'}
        
        if mode == 'create':
            return {
                'success': True,
                'preview': code,
                'action': f'Create {filename}'
            }
        
        with open(filepath, 'r', encoding='utf-8') as f:
            original = f.read()
        
        # Simulate injection logic without writing
        if mode == 'replace':
            preview = code
            action = f'Replace entire {filename}'
        elif mode == 'append':
            preview = original + '\n\n' + code
            action = f'Append to {filename}'
        else:
            preview = original  # More complex modes need full simulation
            action = f'{mode} in {filename}'
        
        diff = self._generate_diff(original, preview, filename)
        
        return {
            'success': True,
            'preview': preview,
            'diff': diff,
            'action': action
        }
