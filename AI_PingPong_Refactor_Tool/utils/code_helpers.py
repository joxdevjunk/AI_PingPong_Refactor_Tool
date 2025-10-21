"""
Code Helpers - Parsing signatures Python.
Extrait de main.py.
"""

import re


class CodeHelpers:
    """Helpers pour parsing code Python."""
    
    @staticmethod
    def extract_params_from_signature(signature: str) -> list[str]:
        """
        Extract parameter names from method signature.
        
        Example:
            "method(self, x: int, y: str = 'default')" 
            -> ["self", "x", "y"]
        """
        match = re.search(r'\((.*?)\)', signature)
        if not match:
            return []
        
        params_str = match.group(1).strip()
        if not params_str:
            return []
        
        params = []
        current_param = ''
        bracket_depth = 0
        paren_depth = 0
        
        for char in params_str + ',':
            if char == '[':
                bracket_depth += 1
                current_param += char
            elif char == ']':
                bracket_depth -= 1
                current_param += char
            elif char == '(':
                paren_depth += 1
                current_param += char
            elif char == ')':
                paren_depth -= 1
                current_param += char
            elif char == ',' and bracket_depth == 0 and paren_depth == 0:
                param = current_param.strip()
                if param:
                    cleaned = CodeHelpers._clean_param(param)
                    if cleaned:
                        params.append(cleaned)
                current_param = ''
            else:
                current_param += char
        
        return params
    
    @staticmethod
    def _clean_param(param: str) -> str:
        """Clean parameter (remove type hints, defaults)."""
        param = param.strip()
        if not param:
            return None
        
        # Keep *args and **kwargs as-is
        if param.startswith('*') or param.startswith('**'):
            if ':' in param:
                param = param.split(':')[0].strip()
            if '=' in param:
                param = param.split('=')[0].strip()
            return param
        
        # Remove type hints
        if ':' in param:
            param = param.split(':')[0].strip()
        
        # Remove defaults
        if '=' in param:
            param = param.split('=')[0].strip()
        
        return param
