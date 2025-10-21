"""
Strategies pour parser réponses JSON de l'IA.
Extrait de main.py lignes 1701-2800.
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime


class ParsingStrategy(ABC):
    """Interface base pour strategies de parsing."""
    
    @abstractmethod
    def can_handle(self, response_text: str) -> bool:
        """Détecte si cette stratégie peut parser la réponse."""
        pass
    
    @abstractmethod
    def parse(self, response_text: str, context: Optional[Dict] = None) -> List[Dict]:
        """Parse la réponse en liste de tasks."""
        pass


class SimpleTaskParsingStrategy(ParsingStrategy):
    """
    Parse format simple: {"tasks": [...]}
    Ancien format pour bugs/features.
    """
    
    def can_handle(self, response_text: str) -> bool:
        """Détecte format simple tasks."""
        try:
            data = json.loads(response_text)
            return 'tasks' in data and isinstance(data['tasks'], list)
        except (json.JSONDecodeError, KeyError):
            return False
    
    def parse(self, response_text: str, context: Optional[Dict] = None) -> List[Dict]:
        """Parse tasks simples."""
        data = json.loads(response_text)
        ai_tasks = data.get('tasks', [])
        
        tasks = []
        for task_data in ai_tasks:
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
                'source': 'ai_simple_task',
                'source_file': context.get('analyzed_file', 'unknown.py') if context else 'unknown.py'
            }
            tasks.append(task)
        
        return tasks


class RefactoringParsingStrategy(ParsingStrategy):
    """
    Parse format refactoring complexe.
    Keys: critical_issues_prioritized, immediate_quick_wins, targeted_refactoring_plan
    """
    
    def can_handle(self, response_text: str) -> bool:
        """Détecte format refactoring."""
        try:
            data = json.loads(response_text)
            return any(key in data for key in [
                'critical_issues_prioritized',
                'immediate_quick_wins',
                'targeted_refactoring_plan'
            ])
        except (json.JSONDecodeError, KeyError):
            return False
    
    def parse(self, response_text: str, context: Optional[Dict] = None) -> List[Dict]:
        """Parse analyse refactoring complète."""
        data = json.loads(response_text)
        source_file = context.get('analyzed_file', 'unknown.py') if context else 'unknown.py'
        
        tasks = []
        task_counter = 0
        
        # === 1. CRITICAL ISSUES ===
        if 'critical_issues_prioritized' in data:
            for issue in data['critical_issues_prioritized']:
                task_counter += 1
                tasks.append(self._build_critical_issue_task(issue, task_counter, source_file))
        
        # === 2. QUICK WINS ===
        if 'immediate_quick_wins' in data:
            for action in data['immediate_quick_wins']:
                task_counter += 1
                tasks.append(self._build_quick_win_task(action, task_counter, source_file))
        
        # === 3. PHASED PLAN (EPICS) ===
        if 'targeted_refactoring_plan' in data:
            epic_tasks = self._build_epic_tasks(data['targeted_refactoring_plan'], source_file)
            tasks.extend(epic_tasks)
        
        return tasks
    
    def _build_critical_issue_task(self, issue: Dict, counter: int, source_file: str) -> Dict:
        """Build task depuis critical issue."""
        priority_str = issue.get('priority', 'P1')
        if 'P0' in priority_str:
            icon = '🔴'
            priority = 'critical'
        elif 'P1' in priority_str:
            icon = '⚠️'
            priority = 'high'
        else:
            icon = '🔶'
            priority = 'medium'
        
        description = f"{issue['description']}\n\n"
        description += f"**Impact:** {issue.get('impact', 'N/A')}\n\n"
        description += f"**Solution:** {issue.get('solution', 'N/A')}\n\n"
        
        if 'affected_methods' in issue:
            methods = issue['affected_methods']
            if isinstance(methods, list) and methods:
                description += f"**Méthodes ({len(methods)}):** "
                description += ", ".join(f"`{m}`" for m in methods[:5])
                if len(methods) > 5:
                    description += f" ... +{len(methods)-5}"
                description += "\n\n"
        
        return {
            'id': f"REFACTOR_{counter}",
            'title': f"{icon} {issue['issue']}",
            'description': description.strip(),
            'priority': priority,
            'status': 'todo',
            'effort': issue.get('effort', 'Unknown'),
            'category': issue.get('category', 'refactoring'),
            'tags': ['refactoring', priority_str.lower()],
            'source': 'ai_refactoring',
            'source_file': source_file,
            'created_at': datetime.now().isoformat()
        }
    
    def _build_quick_win_task(self, action: Dict, counter: int, source_file: str) -> Dict:
        """Build task depuis quick win."""
        priority_map = {'P0': 'critical', 'P1': 'high', 'P2': 'medium'}
        priority = priority_map.get(action.get('priority', 'P2'), 'medium')
        
        description = f"⚡ **Quick Win** - Temps: {action.get('effort', 'Unknown')}\n\n"
        description += f"**Impact:** {action.get('impact', 'N/A')}\n\n"
        
        if 'steps' in action:
            description += "**Steps:**\n"
            for i, step in enumerate(action['steps'], 1):
                description += f"{i}. {step}\n"
        
        return {
            'id': f"QUICKWIN_{counter}",
            'title': f"⚡ {action['action']}",
            'description': description.strip(),
            'priority': priority,
            'status': 'todo',
            'effort': action.get('effort', 'Unknown'),
            'category': 'quick_win',
            'tags': ['quick-win', 'refactoring'],
            'source': 'ai_refactoring',
            'source_file': source_file,
            'created_at': datetime.now().isoformat()
        }
    
    def _build_epic_tasks(self, plan: Dict, source_file: str) -> List[Dict]:
        """Build epic tasks depuis phased plan."""
        tasks = []
        
        for phase_key, phase_data in plan.items():
            if phase_key == 'philosophy' or not isinstance(phase_data, dict):
                continue
            
            description = f"**Goal:** {phase_data.get('goal', 'N/A')}\n"
            description += f"**Duration:** {phase_data.get('duration', 'Unknown')}\n\n"
            
            if 'tasks' in phase_data and isinstance(phase_data['tasks'], list):
                description += f"**Subtasks ({len(phase_data['tasks'])}):**\n"
                for subtask in phase_data['tasks']:
                    description += f"• {subtask}\n"
            
            tasks.append({
                'id': f"EPIC_{phase_key}",
                'title': f"📦 {phase_data.get('goal', phase_key.title())}",
                'description': description.strip(),
                'priority': 'high' if 'P0' in phase_data.get('priority', '') else 'medium',
                'status': 'todo',
                'effort': phase_data.get('duration', 'Unknown'),
                'category': 'epic',
                'tags': ['epic', 'refactoring', phase_key],
                'source': 'ai_refactoring',
                'source_file': source_file,
                'created_at': datetime.now().isoformat()
            })
        
        return tasks


class ResponseParser:
    """
    Context qui utilise strategies pour parser réponses AI.
    Auto-détecte format et applique bonne stratégie.
    """
    
    def __init__(self):
        self.strategies: List[ParsingStrategy] = [
            SimpleTaskParsingStrategy(),
            RefactoringParsingStrategy(),
        ]
    
    def parse(self, response_text: str, context: Optional[Dict] = None) -> List[Dict]:
        """
        Parse réponse AI automatiquement.
        
        Args:
            response_text: JSON brut (peut contenir ``````)
            context: {'analyzed_file': 'main.py', ...}
        
        Returns:
            List of normalized tasks
        
        Raises:
            ValueError: Si aucune stratégie compatible
        """
        # Extract JSON from markdown
        clean_json = self._extract_json(response_text)
        
        # Try strategies
        for strategy in self.strategies:
            if strategy.can_handle(clean_json):
                return strategy.parse(clean_json, context)
        
        # No strategy found
        raise ValueError(
            "Unknown response format.\n\n"
            "Expected either:\n"
            "• {'tasks': [...]}\n"
            "• {'critical_issues_prioritized': [...], ...}"
        )
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from markdown code block or raw text."""
        # Try markdown block
        match = re.search(r'``````', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Try raw JSON
        text = text.strip()
        if text.startswith('{') or text.startswith('['):
            return text
        
        raise ValueError("No JSON found in response")
    
    def add_strategy(self, strategy: ParsingStrategy):
        """Add custom strategy (extensibility)."""
        self.strategies.insert(0, strategy)


# === TESTS ===
if __name__ == '__main__':
    parser = ResponseParser()
    
    # Test simple format
    simple_json = '''
    {
        "tasks": [
            {
                "title": "Fix crash",
                "description": "App crashes on startup",
                "priority": "high",
                "methods": []
            }
        ]
    }
    '''
    
    tasks = parser.parse(simple_json, {'analyzed_file': 'main.py'})
    assert len(tasks) == 1
    assert tasks[0]['title'] == "Fix crash"
    assert tasks[0]['source_file'] == 'main.py'
    print("✅ Simple parsing OK")
    
    # Test refactoring format
    refactor_json = '''
    {
        "critical_issues_prioritized": [
            {
                "priority": "P0 - Urgent",
                "issue": "God Class",
                "description": "SimplePingPongGUI has 1983 lines",
                "impact": "Unmaintainable",
                "solution": "Extract panels",
                "effort": "2-3 days",
                "category": "architecture"
            }
        ]
    }
    '''
    
    tasks = parser.parse(refactor_json, {'analyzed_file': 'main.py'})
    assert len(tasks) == 1
    assert tasks[0]['priority'] == 'critical'
    assert '🔴' in tasks[0]['title']
    print("✅ Refactoring parsing OK")
