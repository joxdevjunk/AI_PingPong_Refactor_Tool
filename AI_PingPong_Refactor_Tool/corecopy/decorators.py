"""
Système de décorateurs configurable pour ai_Pingpong.
Permet de contrôler finement le logging et la détection de problèmes.
"""

import functools
import logging
import time
import traceback
import inspect
from typing import Callable, Optional, Any
from enum import Enum
from pathlib import Path

# ============================================================================
# CONFIGURATION GLOBALE - Modifiable à la volée
# ============================================================================

class LogConfig:
    """Configuration globale du système de logging."""
    
    # Activer/désactiver fonctionnalités
    ENABLED = True
    TRACE_CALLS = True
    DETECT_LOOPS = True
    SHOW_ARGS = True
    SHOW_RETURNS = True
    SHOW_TIMING = True
    SHOW_CALLER = False  # Peut ralentir si activé partout
    SHOW_STACK_ON_LOOP = True
    
    # Niveaux de verbosité
    DEFAULT_LEVEL = logging.DEBUG
    LOOP_WARNING_LEVEL = logging.WARNING
    ERROR_LEVEL = logging.ERROR
    
    # Limites
    MAX_ARG_LENGTH = 100  # Tronquer arguments trop longs
    MAX_RETURN_LENGTH = 50
    LOOP_MAX_CALLS = 3
    LOOP_WINDOW_SECONDS = 1.0
    STACK_LIMIT = 8
    
    # Filtres de fichiers/fonctions
    EXCLUDE_FILES = []  # Ex: ['PyQt6', 'site-packages']
    ONLY_FILES = []  # Si spécifié, log seulement ces fichiers
    EXCLUDE_FUNCTIONS = []  # Ex: ['paintEvent', 'resizeEvent']
    
    # Format output
    USE_EMOJIS = True
    INDENT_NESTED_CALLS = True
    COLOR_OUTPUT = False  # Nécessite colorama si True
    
    # Fichier log
    LOG_TO_FILE = True
    LOG_FILE_PATH = Path('.ai_pingpong_debug.log')
    LOG_FILE_MAX_SIZE_MB = 10


# ============================================================================
# UTILITAIRES
# ============================================================================

class _CallDepth:
    """Tracker pour l'indentation des appels imbriqués."""
    depth = 0
    
    @classmethod
    def indent(cls):
        return "  " * cls.depth if LogConfig.INDENT_NESTED_CALLS else ""


def _should_log_function(func: Callable) -> bool:
    """Détermine si la fonction doit être loggée selon les filtres."""
    if not LogConfig.ENABLED:
        return False
    
    # Vérifier exclusions
    if func.__name__ in LogConfig.EXCLUDE_FUNCTIONS:
        return False
    
    # Récupérer le fichier source
    try:
        source_file = inspect.getfile(func)
        
        # Exclure certains fichiers
        if any(exclude in source_file for exclude in LogConfig.EXCLUDE_FILES):
            return False
        
        # Si ONLY_FILES spécifié, vérifier inclusion
        if LogConfig.ONLY_FILES:
            return any(only in source_file for only in LogConfig.ONLY_FILES)
    except:
        pass
    
    return True


def _format_value(value: Any, max_length: int = None) -> str:
    """Formate une valeur pour affichage (avec troncature)."""
    if max_length is None:
        max_length = LogConfig.MAX_ARG_LENGTH
    
    repr_val = repr(value)
    if len(repr_val) > max_length:
        return repr_val[:max_length] + '...'
    return repr_val


def _get_caller_info():
    """Récupère info sur la fonction appelante."""
    if not LogConfig.SHOW_CALLER:
        return ""
    
    try:
        frame = inspect.currentframe().f_back.f_back.f_back
        info = inspect.getframeinfo(frame)
        filename = Path(info.filename).name
        return f" [from {filename}:{info.lineno} in {frame.f_code.co_name}()]"
    except:
        return ""


def _get_logger(func: Callable) -> logging.Logger:
    """Récupère ou crée le logger approprié."""
    return logging.getLogger(func.__module__)


# ============================================================================
# DÉCORATEURS PRINCIPAUX
# ============================================================================

def trace_calls(
    level: int = None,
    show_args: bool = None,
    show_returns: bool = None,
    show_timing: bool = None,
    custom_message: str = None
):
    """
    Décorateur principal pour tracer les appels de fonction.
    
    Args:
        level: Niveau de log (logging.DEBUG, INFO, etc.)
        show_args: Afficher les arguments (override config)
        show_returns: Afficher les retours (override config)
        show_timing: Afficher le timing (override config)
        custom_message: Message custom au lieu du format par défaut
    
    Usage:
        @trace_calls()
        def my_method(self, x, y):
            return x + y
        
        @trace_calls(level=logging.INFO, show_args=False)
        def sensitive_method(self, password):
            # Arguments masqués
            pass
    """
    def decorator(func: Callable) -> Callable:
        if not _should_log_function(func):
            return func
        
        logger = _get_logger(func)
        log_level = level if level is not None else LogConfig.DEFAULT_LEVEL
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not LogConfig.TRACE_CALLS:
                return func(*args, **kwargs)
            
            # Configuration locale (override global)
            _show_args = show_args if show_args is not None else LogConfig.SHOW_ARGS
            _show_returns = show_returns if show_returns is not None else LogConfig.SHOW_RETURNS
            _show_timing = show_timing if show_timing is not None else LogConfig.SHOW_TIMING
            
            # Construire le message d'entrée
            indent = _CallDepth.indent()
            emoji = "→" if LogConfig.USE_EMOJIS else ">"
            
            if custom_message:
                entry_msg = f"{indent}{emoji} {custom_message}"
            else:
                # Formatter arguments
                signature = ""
                if _show_args:
                    # Skip self/cls
                    args_list = [_format_value(a) for a in args[1:]]
                    kwargs_list = [f"{k}={_format_value(v)}" for k, v in kwargs.items()]
                    signature = ", ".join(args_list + kwargs_list)
                
                caller_info = _get_caller_info()
                entry_msg = f"{indent}{emoji} {func.__name__}({signature}){caller_info}"
            
            logger.log(log_level, entry_msg)
            
            # Incrémenter profondeur
            _CallDepth.depth += 1
            
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                
                # Message de sortie
                exit_emoji = "←" if LogConfig.USE_EMOJIS else "<"
                exit_msg = f"{indent}{exit_emoji} {func.__name__}"
                
                if _show_returns and result is not None:
                    result_str = _format_value(result, LogConfig.MAX_RETURN_LENGTH)
                    exit_msg += f" → {result_str}"
                
                if _show_timing:
                    exit_msg += f" [{duration*1000:.1f}ms]"
                
                logger.log(log_level, exit_msg)
                return result
                
            except Exception as e:
                duration = time.perf_counter() - start
                error_emoji = "✗" if LogConfig.USE_EMOJIS else "X"
                
                logger.log(
                    LogConfig.ERROR_LEVEL,
                    f"{indent}{error_emoji} {func.__name__} raised {type(e).__name__} "
                    f"after {duration*1000:.1f}ms: {e}",
                    exc_info=True
                )
                raise
            
            finally:
                _CallDepth.depth -= 1
        
        return wrapper
    return decorator


def detect_loops(max_calls: int = None, window_seconds: float = None, action: str = 'warn'):
    """
    Détecte les boucles d'appels (appels répétés suspects).
    
    Args:
        max_calls: Nombre max d'appels dans la fenêtre (défaut: config)
        window_seconds: Taille de la fenêtre temporelle (défaut: config)
        action: 'warn' (warning), 'raise' (exception), 'ignore'
    
    Usage:
        @detect_loops(max_calls=2, window_seconds=0.5)
        def refresh(self):
            pass
        
        @detect_loops(max_calls=5, action='raise')
        def critical_method(self):
            pass
    """
    def decorator(func: Callable) -> Callable:
        if not _should_log_function(func) or not LogConfig.DETECT_LOOPS:
            return func
        
        logger = _get_logger(func)
        _max_calls = max_calls if max_calls is not None else LogConfig.LOOP_MAX_CALLS
        _window = window_seconds if window_seconds is not None else LogConfig.LOOP_WINDOW_SECONDS
        
        # Stockage des appels récents
        func._recent_calls = []
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # Nettoyer vieux appels hors fenêtre
            func._recent_calls = [t for t in func._recent_calls if now - t < _window]
            
            # Détecter boucle
            if len(func._recent_calls) >= _max_calls:
                call_count = len(func._recent_calls) + 1
                emoji = "⚠️" if LogConfig.USE_EMOJIS else "!!"
                
                msg = (
                    f"{emoji} LOOP DETECTED: {func.__name__} called {call_count} times "
                    f"in {_window}s (max: {_max_calls})"
                )
                
                if action == 'warn':
                    logger.log(LogConfig.LOOP_WARNING_LEVEL, msg)
                    
                    if LogConfig.SHOW_STACK_ON_LOOP:
                        logger.log(LogConfig.LOOP_WARNING_LEVEL, "Call stack:")
                        traceback.print_stack(limit=LogConfig.STACK_LIMIT)
                
                elif action == 'raise':
                    logger.error(msg)
                    traceback.print_stack(limit=LogConfig.STACK_LIMIT)
                    raise RecursionError(f"{func.__name__} loop detected")
                
                # action == 'ignore' : ne rien faire
            
            # Enregistrer l'appel
            func._recent_calls.append(now)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def profile_slow(threshold_ms: float = 100.0):
    """
    Log un warning si la fonction prend plus que le seuil.
    
    Args:
        threshold_ms: Seuil en millisecondes
    
    Usage:
        @profile_slow(threshold_ms=50.0)
        def expensive_operation(self):
            # Si > 50ms, warning automatique
            pass
    """
    def decorator(func: Callable) -> Callable:
        if not _should_log_function(func):
            return func
        
        logger = _get_logger(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            
            if duration_ms > threshold_ms:
                emoji = "🐌" if LogConfig.USE_EMOJIS else "SLOW"
                logger.warning(
                    f"{emoji} {func.__name__} took {duration_ms:.1f}ms "
                    f"(threshold: {threshold_ms:.1f}ms)"
                )
            
            return result
        
        return wrapper
    return decorator


def count_calls(reset_on_max: bool = True):
    """
    Compte les appels à la fonction (utile pour debug).
    
    Args:
        reset_on_max: Reset compteur si atteint sys.maxsize
    
    Usage:
        @count_calls()
        def frequently_called_method(self):
            pass
        
        # Accéder au compteur:
        print(frequently_called_method.call_count)
    """
    def decorator(func: Callable) -> Callable:
        func.call_count = 0
        func.reset_count = lambda: setattr(func, 'call_count', 0)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func.call_count += 1
            
            if reset_on_max and func.call_count >= 2**31:
                func.call_count = 0
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# DÉCORATEURS COMBINÉS (PRESETS)
# ============================================================================

def debug_method(level=logging.DEBUG):
    """Preset: trace complet pour debugging."""
    def decorator(func):
        @detect_loops(max_calls=3)
        @trace_calls(level=level, show_args=True, show_returns=True, show_timing=True)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def monitor_performance(threshold_ms=100.0):
    """Preset: monitoring performance simple."""
    def decorator(func):
        @profile_slow(threshold_ms=threshold_ms)
        @trace_calls(show_args=False, show_timing=True)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def critical_section():
    """Preset: section critique avec détection boucle stricte."""
    def decorator(func):
        @detect_loops(max_calls=1, action='raise')
        @trace_calls(level=logging.WARNING)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# UTILITAIRES DE CONFIGURATION
# ============================================================================

def configure(
    enabled: bool = None,
    level: int = None,
    detect_loops: bool = None,
    log_file: Path = None,
    **kwargs
):
    """
    Configure le système de logging globalement.
    
    Usage:
        # Au début de main.py
        from core.decorators import configure, LogConfig
        
        configure(
            enabled=True,
            level=logging.INFO,
            detect_loops=True,
            log_file=Path('.logs/ai_pingpong.log')
        )
    """
    if enabled is not None:
        LogConfig.ENABLED = enabled
    if level is not None:
        LogConfig.DEFAULT_LEVEL = level
    if detect_loops is not None:
        LogConfig.DETECT_LOOPS = detect_loops
    if log_file is not None:
        LogConfig.LOG_FILE_PATH = log_file
    
    for key, value in kwargs.items():
        if hasattr(LogConfig, key.upper()):
            setattr(LogConfig, key.upper(), value)


def enable():
    """Active le système de logging."""
    LogConfig.ENABLED = True


def disable():
    """Désactive le système de logging."""
    LogConfig.ENABLED = False


def stats():
    """Affiche les stats des fonctions décorées avec @count_calls."""
    import sys
    
    print("\n" + "="*60)
    print("CALL STATISTICS")
    print("="*60)
    
    for name, obj in sys.modules[__name__].__dict__.items():
        if callable(obj) and hasattr(obj, 'call_count'):
            print(f"{name:40s} : {obj.call_count:>10,} calls")
    
    print("="*60 + "\n")
