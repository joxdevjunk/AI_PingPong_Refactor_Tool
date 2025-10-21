"""
Prompt Generator - Generate prompts from templates.
Extrait de main.py generate_prompt() (L963-1169).
"""

from typing import List, Dict, Optional
from pathlib import Path

class PromptGenerator:
    """
    Génère prompts depuis templates Jinja2.
    Code extrait SANS modification de main.py.
    """
    
    def __init__(self, composer, analysis):
        self.composer = composer
        self.analysis = analysis
    
    def _to_dict(self, obj):
        """Convertit récursivement objet en dict pur."""
        if isinstance(obj, dict):
            return {k: self._to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._to_dict(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._to_dict(obj.__dict__)
        else:
            return obj
    
    def generate_refactor_file(self, target_file: str, file_methods: List) -> str:
        """
        Génère prompt refactor_file.
        COPIÉ de generate_prompt() mode refactor_file.
        """
        from corecopy.file_analyzer import FileAnalyzer
        
        # Build file summary
        file_summary_obj = FileAnalyzer.build_summary(target_file, {'classes': self._group_methods_by_class(file_methods)})
        
        # Convertir en dict pur pour Jinja2
        file_summary_data = self._to_dict(file_summary_obj)
        print(f"\n=== DEBUG FILE_SUMMARY ===")
        print(f"Type: {type(file_summary_data)}")
        print(f"Keys: {file_summary_data.keys() if isinstance(file_summary_data, dict) else 'NOT A DICT'}")
        if isinstance(file_summary_data, dict) and 'metrics' in file_summary_data:
            print(f"Type metrics: {type(file_summary_data['metrics'])}")
            print(f"Metrics: {file_summary_data['metrics']}")
        print("=========================\n")
        # Build context
        context = {
            'project_name': self.analysis['project_name'],
            'file_summary': file_summary_data
        }
        
        # Render template
        prompt = self.composer.render(
            'prompts/refactor_file.jinja2',
            **context
        )
        
        return prompt
    
    def generate_normal(self, template: str, selected_tasks: List[Dict], 
                       description: str, code_mode: bool) -> str:
        """
        Génère prompt normal (debug_bug, feature_new, refactor_code).
        COPIÉ de generate_prompt() mode normal.
        """
        # Build context
        context = {
            'project_name': self.analysis['project_name'],
            'selected_tasks': selected_tasks,
            'num_tasks': len(selected_tasks),
            'code_mode': code_mode
        }
        
        # Add template-specific variables
        if template == 'debug_bug':
            context['bug_description'] = description or "⚠️ Describe the bug"
            context['traceback'] = ""
        elif template == 'feature_new':
            context['feature_description'] = description or "⚠️ Describe the feature"
        elif template == 'refactor_code':
            context['refactor_goal'] = description or "⚠️ Describe refactor goal"
        
        # Render
        prompt = self.composer.render(
            f'prompts/{template}.jinja2',
            **context
        )
        
        return prompt
    
    def _group_methods_by_class(self, methods: List) -> Dict:
        """Group methods par classe."""
        classes = {}
        for method in methods:
            class_name = method.class_name  # ← AJOUTE ICI
            
            if class_name not in classes:
                classes[class_name] = {
                    'name': class_name,
                    'methods': []
                }
            
            # CALCULE metrics depuis le code
            code_lines = len([l for l in method.code.split('\n') if l.strip() and not l.strip().startswith('#')])
            total_lines = len(method.code.split('\n'))
            
            classes[class_name]['methods'].append({
                'name': method.method_name,
                'method_name': method.method_name,
                'signature': method.signature,
                'docstring': method.docstring,
                'lineno': method.lineno,
                'code': method.code,
                'metrics': {
                    'code_lines': code_lines,
                    'total_lines': total_lines
                }
            })
        return classes
