"""
File Analyzer - Build detailed file summaries.
Extrait de main.py _build_file_summary_data() (L1630-1803).
"""

import json
from datetime import datetime
from typing import Dict, List


class FileAnalyzer:
    """
    Analyse détaillée fichier Python.
    Code extrait SANS modification de main.py.
    """
    
    @staticmethod
    def build_summary(file_path: str, file_data: Dict) -> Dict:
        """
        Build summary depuis analysis data.
        COPIÉ EXACTEMENT de _build_file_summary_data L1630-1803.
        """
        classes_data = []
        total_methods = 0
        total_code_lines = 0
        total_lines_all = 0
        method_lengths = []
        undocumented = 0
        long_methods = []
        complexity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for class_name, class_info in file_data.get('classes', {}).items():
            methods = class_info.get('methods', [])
            
            methods_data = []
            class_total_lines = 0
            class_code_lines = 0
            
            for method in methods:
                total_methods += 1
                
                # Extract params
                params = FileAnalyzer._extract_params_from_signature(method.get('signature', ''))
                
                # Detect signals
                signals = FileAnalyzer._detect_signals_in_code(method.get('code', ''))
                
                # Clean docstring
                docstring = method.get('docstring', '').strip() if method.get('docstring') else "No docstring"
                has_docstring = bool(method.get('docstring'))
                if not has_docstring:
                    undocumented += 1
                
                if '\n' in docstring:
                    docstring = docstring.split('\n')[0].strip()
                if len(docstring) > 120:
                    docstring = docstring[:117] + "..."
                
                # Metrics
                metrics = method.get('metrics', {})
                code_lines = metrics.get('code_lines', 0)
                total_line = metrics.get('total_lines', 0)
                
                class_total_lines += total_line
                class_code_lines += code_lines
                total_code_lines += code_lines
                total_lines_all += total_line
                method_lengths.append(code_lines)
                
                # Complexity
                complexity = 'low'
                if code_lines > 100:
                    complexity = 'critical'
                elif code_lines > 50:
                    complexity = 'high'
                elif code_lines > 20:
                    complexity = 'medium'
                
                complexity_counts[complexity] += 1
                
                # Long methods
                if code_lines > 50:
                    long_methods.append({
                        'name': method.get('method_name'),
                        'lines': code_lines,
                        'start': method.get('lineno', 0),
                        'end': method.get('lineno', 0) + total_line
                    })
                
                method_metrics = FileAnalyzer._method_metrics(method.get('method_name'), metrics)
                
                methods_data.append({
                    'signature': method.get('signature'),
                    'name': method.get('method_name'),
                    'docstring': docstring,
                    'has_docstring': has_docstring,
                    'params': params,
                    'params_str': ', '.join(params) if params else None,
                    'signals': signals,
                    'signals_str': ', '.join(signals) if signals else None,
                    'complexity': complexity,
                    'is_long': code_lines > 50,
                    'is_complex': code_lines > 20,
                    **method_metrics
                })
            
            classes_data.append({
                'name': class_name,
                'is_module': (class_name == 'MODULE'),
                'methods': methods_data,
                'method_count': len(methods_data),
                'total_lines': class_total_lines,
                'code_lines': class_code_lines
            })
        
        # Calculate metrics
        avg_length = sum(method_lengths) / len(method_lengths) if method_lengths else 0
        median_length = sorted(method_lengths)[len(method_lengths) // 2] if method_lengths else 0
        undoc_pct = (undocumented / total_methods * 100) if total_methods > 0 else 0
        
        return {
            'file_path': file_path,
            'total_methods': total_methods,
            'total_classes': len(classes_data),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'classes': classes_data,
            'metrics': {
                'total_code_lines': total_code_lines,
                'total_lines': total_lines_all,
                'average_method_length': round(avg_length, 1),
                'median_method_length': median_length,
                'undocumented_count': undocumented,
                'undocumented_percentage': round(undoc_pct, 1),
                'long_methods_count': len(long_methods),
                'long_methods': long_methods[:5],  # Top 5
                'complexity_distribution': complexity_counts
            }
        }

    @staticmethod
    def _extract_params_from_signature(signature: str) -> List[str]:
        """Extract parameter names (COPIÉ de extract_params_from_signature)."""
        import re
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
                    cleaned = FileAnalyzer._clean_param(param)
                    if cleaned:
                        params.append(cleaned)
                current_param = ''
            else:
                current_param += char
        
        return params
    
    @staticmethod
    def _clean_param(param: str) -> str:
        """Clean parameter name (COPIÉ de clean_param)."""
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
    
    @staticmethod
    def _detect_signals_in_code(code: str) -> List[str]:
        """Detect Qt signals (COPIÉ de detect_signals_in_code)."""
        import re
        if not code:
            return []
        
        pattern = r'self\.(\w+)\.emit'
        matches = re.findall(pattern, code)
        return sorted(set(matches))
    
    @staticmethod
    def _method_metrics(method_name: str, metrics: Dict) -> Dict:
        """Extract method metrics."""
        return {
            'start_line': metrics.get('start_line'),
            'end_line': metrics.get('end_line'),
            'total_lines': metrics.get('total_lines'),
            'code_lines': metrics.get('code_lines'),
            'comment_lines': metrics.get('comment_lines'),
            'complexity': metrics.get('complexity'),
            'has_docstring': bool(metrics.get('docstring')),
            'is_long': metrics.get('code_lines', 0) > 50,
            'is_complex': metrics.get('complexity') in ('high', 'critical')
        }
