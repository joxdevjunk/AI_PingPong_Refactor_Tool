"""
Prompt Composer - Génération prompts via Jinja2
"""

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pathlib import Path
from typing import Dict, List, Any
import re


class PromptComposer:
    """Compose prompts depuis templates Jinja2."""
    
    def __init__(self, templates_dir: str = 'templates'):
        # PATH HACK ABSOLU: toujours depuis ce fichier
        base_dir = Path(__file__).parent.parent.resolve()  # core/ -> racine projet
        self.templates_dir = base_dir / templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirs
        (self.templates_dir / 'prompts').mkdir(exist_ok=True)
        (self.templates_dir / 'sections').mkdir(exist_ok=True)
        
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

    
    def render(self, template_name: str, **kwargs) -> str:
        """Rend un template avec variables."""
        try:
            template = self.env.get_template(template_name)
            return template.render(**kwargs)
        except TemplateNotFound:
            return f"ERROR: Template '{template_name}' not found!"
        except Exception as e:
            return f"ERROR rendering template: {e}"
    
    def list_templates(self, category: str = 'prompts') -> List[str]:
        """Liste templates disponibles dans catégorie."""
        template_dir = self.templates_dir / category
        if not template_dir.exists():
            return []
        
        return [f.stem for f in template_dir.glob('*.jinja2')]
    
    def get_template_variables(self, template_name: str) -> List[str]:
        """Extrait variables d'un template."""
        try:
            template_path = self.templates_dir / template_name
            if not template_path.exists():
                return []
            
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex pour {{ var }} et {% for var in %}
            variables = set()
            
            # {{ variable }}
            for match in re.finditer(r'\{\{\s*(\w+)', content):
                variables.add(match.group(1))
            
            # {% for var in ... %}
            for match in re.finditer(r'\{%\s*for\s+(\w+)\s+in', content):
                variables.add(match.group(1))
            
            return sorted(list(variables))
        except Exception as e:
            print(f"Error extracting variables: {e}")
            return []
    
    def render_prompt(self, 
                     template_type: str,
                     project_name: str,
                     selected_tasks: List[Any],
                     **extra_vars) -> str:
        """Rend prompt complet avec contexte."""
        
        template_path = f"prompts/{template_type}.jinja2"
        
        context = {
            'project_name': project_name,
            'selected_tasks': selected_tasks,
            'num_tasks': len(selected_tasks),
            **extra_vars
        }
        
        return self.render(template_path, **context)
    
    def create_template(self, name: str, content: str, category: str = 'prompts'):
        """Crée un nouveau template."""
        template_dir = self.templates_dir / category
        template_dir.mkdir(exist_ok=True)
        
        template_path = template_dir / f"{name}.jinja2"
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(template_path)
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Info sur un template."""
        template_path = self.templates_dir / template_name
        
        if not template_path.exists():
            return {'exists': False}
        
        variables = self.get_template_variables(template_name)
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'exists': True,
            'path': str(template_path),
            'variables': variables,
            'size': len(content),
            'lines': content.count('\n') + 1
        }
