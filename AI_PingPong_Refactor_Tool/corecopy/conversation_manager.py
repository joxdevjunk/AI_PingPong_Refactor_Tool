"""
Conversation Manager - Gestion historique ping-pong
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Cycle:
    """Représente un cycle ping-pong."""
    cycle_number: int
    prompt: str
    response: Dict
    timestamp: str
    needs_detected: List[str]
    is_converged: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Cycle':
        return cls(**data)


class ConversationManager:
    """Gère conversations ping-pong."""
    
    def __init__(self):
        self.conversations_dir = Path('data/conversations')
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_conversation_id: Optional[str] = None
        self.cycles: List[Cycle] = []
        self.project_name: str = ""
    
    def start_conversation(self, project_name: str) -> str:
        """Démarre nouvelle conversation."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.current_conversation_id = f"{project_name}_{timestamp}"
        self.project_name = project_name
        self.cycles = []
        
        return self.current_conversation_id
    
    def add_cycle(self, 
                  prompt: str,
                  response: Dict,
                  needs_detected: List[str] = None) -> int:
        """Ajoute un cycle à la conversation."""
        
        cycle_number = len(self.cycles) + 1
        
        is_converged = response.get('ready_to_implement', False)
        
        cycle = Cycle(
            cycle_number=cycle_number,
            prompt=prompt,
            response=response,
            timestamp=datetime.now().isoformat(),
            needs_detected=needs_detected or [],
            is_converged=is_converged
        )
        
        self.cycles.append(cycle)
        self._auto_save()
        
        return cycle_number
    
    def get_current_cycle(self) -> int:
        """Retourne numéro cycle courant."""
        return len(self.cycles)
    
    def get_cycle(self, cycle_number: int) -> Optional[Cycle]:
        """Récupère un cycle spécifique."""
        if 0 < cycle_number <= len(self.cycles):
            return self.cycles[cycle_number - 1]
        return None
    
    def get_last_cycle(self) -> Optional[Cycle]:
        """Récupère dernier cycle."""
        if self.cycles:
            return self.cycles[-1]
        return None
    
    def is_converged(self) -> bool:
        """Vérifie si conversation a convergé."""
        last_cycle = self.get_last_cycle()
        return last_cycle.is_converged if last_cycle else False
    
    def get_all_cycles(self) -> List[Cycle]:
        """Retourne tous les cycles."""
        return self.cycles.copy()
    
    def export_history(self, format: str = 'json') -> str:
        """Exporte historique."""
        if format == 'json':
            return self._export_json()
        elif format == 'markdown':
            return self._export_markdown()
        else:
            return ""
    
    def _export_json(self) -> str:
        """Export JSON."""
        data = {
            'conversation_id': self.current_conversation_id,
            'project_name': self.project_name,
            'num_cycles': len(self.cycles),
            'is_converged': self.is_converged(),
            'cycles': [cycle.to_dict() for cycle in self.cycles]
        }
        return json.dumps(data, indent=2)
    
    def _export_markdown(self) -> str:
        """Export Markdown - FIXED."""
        lines = []
        lines.append("# Conversation: " + self.project_name)
        lines.append("**ID**: " + str(self.current_conversation_id))
        lines.append("**Cycles**: " + str(len(self.cycles)))
        lines.append("**Converged**: " + ("Yes" if self.is_converged() else "No"))
        lines.append("")
        
        for cycle in self.cycles:
            prompt_short = cycle.prompt[:500] if len(cycle.prompt) <= 500 else cycle.prompt[:500] + "..."
            resp_json = json.dumps(cycle.response, indent=2)
            resp_short = resp_json[:500] if len(resp_json) <= 500 else resp_json[:500] + "..."
            
            lines.append("## Cycle " + str(cycle.cycle_number))
            lines.append("**Timestamp**: " + cycle.timestamp)
            lines.append("")
            lines.append("### Prompt")
            lines.append(prompt_short)
            lines.append("")
            lines.append("### Response")
            lines.append(resp_short)
            lines.append("")
        
        return "\n".join(lines)

    
    def _auto_save(self):
        """Sauvegarde auto après chaque cycle."""
        if not self.current_conversation_id:
            return
        
        filepath = self.conversations_dir / f"{self.current_conversation_id}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self._export_json())
    
    def load_conversation(self, conversation_id: str) -> bool:
        """Charge une conversation."""
        filepath = self.conversations_dir / f"{conversation_id}.json"
        
        if not filepath.exists():
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_conversation_id = data['conversation_id']
            self.project_name = data['project_name']
            self.cycles = [Cycle.from_dict(c) for c in data['cycles']]
            
            return True
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return False
    
    def list_conversations(self) -> List[Dict]:
        """Liste conversations sauvegardées."""
        conversations = []
        
        for filepath in self.conversations_dir.glob('*.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                conversations.append({
                    'id': data['conversation_id'],
                    'project': data['project_name'],
                    'cycles': data['num_cycles'],
                    'converged': data['is_converged'],
                    'file': filepath.name
                })
            except:
                pass
        
        return sorted(conversations, key=lambda x: x['id'], reverse=True)
    
    def get_stats(self) -> Dict:
        """Stats conversation."""
        return {
            'total_cycles': len(self.cycles),
            'is_converged': self.is_converged(),
            'current_cycle': self.get_current_cycle(),
            'project_name': self.project_name
        }
