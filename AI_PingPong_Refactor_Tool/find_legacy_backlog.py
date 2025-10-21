"""
Fix double backlog display - Supprime ancien système
"""
import re

def fix_main_py():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('main_backup_double.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Backup créé: main_backup_double.py")
    
    # Patterns à supprimer
    patterns_to_remove = [
        # Anciennes créations de widgets
        r'self\.task_list\s*=\s*QListWidget\(\).*?\n',
        r'self\.old_backlog.*?=.*?\n',
        r'self\.backlog_list\s*=\s*QListWidget\(\).*?\n',
        r'self\.backlog_tree\s*=\s*QTreeWidget\(\).*?\n',
        
        # Anciennes insertions dans layout
        r'layout\.addWidget\(self\.task_list\).*?\n',
        r'layout\.addWidget\(self\.old_backlog.*?\).*?\n',
        r'layout\.addWidget\(self\.backlog_list\).*?\n',
    ]
    
    original_length = len(content)
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content)
    
    new_length = len(content)
    
    # Sauvegarder
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {original_length - new_length} caractères supprimés")
    print(f"📄 Fichier main.py nettoyé")
    print("\n🚀 Relance l'app: python main.py")

if __name__ == "__main__":
    fix_main_py()
