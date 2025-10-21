"""
Système d'injection dynamique de décorateurs de debug.
Permet d'ajouter/retirer des décorateurs à runtime sur les méthodes sélectionnées.
"""

import types
import importlib
import sys
from pathlib import Path
from typing import List, Dict, Callable, Any
import logging

from corecopy.decorators import (
    trace_calls, detect_loops, debug_method, 
    monitor_performance, count_calls
)

logger = logging.getLogger(__name__)


class DecoratorInjector:
    """Injecte des décorateurs dynamiquement dans des méthodes existantes."""
    
    # Types de décorateurs disponibles
    DECORATOR_TYPES = {
        'trace': {
            'name': '🔍 Trace Calls',
            'description': 'Log entrée/sortie avec arguments et timing',
            'decorator': lambda: trace_calls(level=logging.DEBUG),
            'color': '#4A90E2'
        },
        'loop_detect': {
            'name': '🔄 Detect Loops',
            'description': 'Détecte les appels répétés (boucles)',
            'decorator': lambda: detect_loops(max_calls=3),
            'color': '#E24A4A'
        },
        'debug_full': {
            'name': '🐛 Full Debug',
            'description': 'Trace + Loop detection + Timing',
            'decorator': lambda: debug_method(),
            'color': '#9B4AE2'
        },
        'performance': {
            'name': '⚡ Performance',
            'description': 'Monitor temps d\'exécution (warning si > 100ms)',
            'decorator': lambda: monitor_performance(threshold_ms=100),
            'color': '#E2A84A'
        },
        'count': {
            'name': '📊 Count Calls',
            'description': 'Compte le nombre d\'appels',
            'decorator': lambda: count_calls(),
            'color': '#4AE2A8'
        }
    }
    
    def __init__(self, project_path: Path):
        """
        Args:
            project_path: Chemin racine du projet à instrumenter
        """
        self.project_path = project_path
        self.instrumented_methods: Dict[str, Dict] = {}  # Key: module.Class.method
        self.original_methods: Dict[str, Callable] = {}  # Backup des méthodes originales
    
    def inject_decorator(
        self, 
        file_path: str, 
        class_name: str, 
        method_name: str,
        decorator_types: List[str]
    ) -> bool:
        """
        Injecte des décorateurs dans une méthode spécifique.
        
        Args:
            file_path: Chemin du fichier Python (ex: 'backlog_tab.py')
            class_name: Nom de la classe (ex: 'BacklogTab')
            method_name: Nom de la méthode (ex: 'refresh')
            decorator_types: Liste des types de décorateurs ('trace', 'loop_detect', etc.)
        
        Returns:
            True si succès, False sinon
        """
        try:
            # Construire identifiant unique
            method_id = f"{file_path}.{class_name}.{method_name}"
            
            # Charger le module
            module = self._load_module(file_path)
            if not module:
                logger.error(f"Failed to load module: {file_path}")
                return False
            
            # Récupérer la classe
            if not hasattr(module, class_name):
                logger.error(f"Class {class_name} not found in {file_path}")
                return False
            
            cls = getattr(module, class_name)
            
            # Récupérer la méthode
            if not hasattr(cls, method_name):
                logger.error(f"Method {method_name} not found in {class_name}")
                return False
            
            original_method = getattr(cls, method_name)
            
            # Backup de la méthode originale si pas déjà fait
            if method_id not in self.original_methods:
                self.original_methods[method_id] = original_method
            else:
                # Restaurer l'original avant de ré-appliquer
                original_method = self.original_methods[method_id]
            
            # Appliquer les décorateurs (ordre inverse pour stack correct)
            decorated_method = original_method
            applied_decorators = []
            
            for dec_type in reversed(decorator_types):
                if dec_type in self.DECORATOR_TYPES:
                    decorator_func = self.DECORATOR_TYPES[dec_type]['decorator']()
                    decorated_method = decorator_func(decorated_method)
                    applied_decorators.append(dec_type)
                    logger.debug(f"Applied {dec_type} decorator to {method_id}")
            
            # Remplacer la méthode dans la classe
            setattr(cls, method_name, decorated_method)
            
            # Enregistrer l'instrumentation
            self.instrumented_methods[method_id] = {
                'file': file_path,
                'class': class_name,
                'method': method_name,
                'decorators': applied_decorators,
                'module': module.__name__
            }
            
            logger.info(f"✅ Instrumented {method_id} with decorators: {applied_decorators}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to inject decorator: {e}", exc_info=True)
            return False
    
    def remove_decorator(self, file_path: str, class_name: str, method_name: str) -> bool:
        """
        Retire les décorateurs d'une méthode (restaure l'original).
        
        Args:
            file_path: Chemin du fichier
            class_name: Nom de la classe
            method_name: Nom de la méthode
        
        Returns:
            True si succès, False sinon
        """
        try:
            method_id = f"{file_path}.{class_name}.{method_name}"
            
            if method_id not in self.original_methods:
                logger.warning(f"Method {method_id} was not instrumented")
                return False
            
            # Charger le module
            module = self._load_module(file_path)
            if not module:
                return False
            
            cls = getattr(module, class_name)
            
            # Restaurer la méthode originale
            original_method = self.original_methods[method_id]
            setattr(cls, method_name, original_method)
            
            # Nettoyer
            del self.instrumented_methods[method_id]
            del self.original_methods[method_id]
            
            logger.info(f"✅ Removed decorators from {method_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove decorator: {e}", exc_info=True)
            return False
    
    def remove_all_decorators(self) -> int:
        """
        Retire tous les décorateurs injectés.
        
        Returns:
            Nombre de méthodes restaurées
        """
        count = 0
        methods_to_remove = list(self.instrumented_methods.keys())
        
        for method_id in methods_to_remove:
            info = self.instrumented_methods[method_id]
            if self.remove_decorator(info['file'], info['class'], info['method']):
                count += 1
        
        return count
    
    def get_instrumented_methods(self) -> List[Dict]:
        """Retourne la liste des méthodes instrumentées."""
        return [
            {
                'id': method_id,
                **info
            }
            for method_id, info in self.instrumented_methods.items()
        ]
    
    def _load_module(self, file_path: str):
        """Charge un module Python dynamiquement."""
        try:
            # Convertir chemin fichier en nom de module
            # Ex: "backlog_tab.py" -> "backlog_tab"
            module_name = Path(file_path).stem
            
            # Ajouter le projet au path si nécessaire
            project_str = str(self.project_path)
            if project_str not in sys.path:
                sys.path.insert(0, project_str)
            
            # Recharger le module si déjà importé
            if module_name in sys.modules:
                return importlib.reload(sys.modules[module_name])
            else:
                return importlib.import_module(module_name)
                
        except Exception as e:
            logger.error(f"Failed to load module {file_path}: {e}")
            return None
    
    def generate_debug_code(
        self,
        file_path: str,
        class_name: str,
        method_name: str,
        decorator_types: List[str]
    ) -> str:
        """
        Génère le code Python avec décorateurs (pour injection permanente).
        
        Returns:
            Code Python avec décorateurs appliqués
        """
        decorators = []
        for dec_type in decorator_types:
            if dec_type == 'trace':
                decorators.append("@trace_calls(level=logging.DEBUG)")
            elif dec_type == 'loop_detect':
                decorators.append("@detect_loops(max_calls=3)")
            elif dec_type == 'debug_full':
                decorators.append("@debug_method()")
            elif dec_type == 'performance':
                decorators.append("@monitor_performance(threshold_ms=100)")
            elif dec_type == 'count':
                decorators.append("@count_calls()")
        
        decorators_str = "\n    ".join(decorators)
        
        return f"""
# Imports nécessaires (ajouter en haut du fichier)
from core.decorators import trace_calls, detect_loops, debug_method, monitor_performance, count_calls
import logging

class {class_name}:
    # ...
    
    {decorators_str}
    def {method_name}(self, ...):
        # Code existant
        pass
"""


# ============================================================================
# HELPER POUR GÉNÉRATION AUTOMATIQUE
# ============================================================================

def generate_debug_file(
    original_file: Path,
    methods_to_debug: List[Dict],
    output_file: Path = None
) -> Path:
    """
    Génère une version du fichier avec décorateurs injectés en dur.
    
    Args:
        original_file: Fichier Python source
        methods_to_debug: Liste de dicts {'class': ..., 'method': ..., 'decorators': [...]}
        output_file: Fichier de sortie (défaut: original_debug.py)
    
    Returns:
        Path du fichier généré
    """
    import ast
    import astor  # Nécessite: pip install astor
    
    if output_file is None:
        output_file = original_file.parent / f"{original_file.stem}_debug.py"
    
    # Parse le fichier source
    with open(original_file, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    tree = ast.parse(source_code)
    
    # TODO: Implémenter transformation AST pour ajouter décorateurs
    # (Complexe, nécessite manipulation d'AST)
    
    # Pour l'instant, version simple: ajouter imports en haut
    imports = """
# AUTO-GENERATED DEBUG IMPORTS
from core.decorators import trace_calls, detect_loops, debug_method, monitor_performance, count_calls
import logging

"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(imports)
        f.write(source_code)
    
    logger.info(f"Generated debug file: {output_file}")
    return output_file
