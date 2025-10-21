"""
Test du ProjectAnalyzer enrichi avec nomenclature
Parse main.py → génère aa.json → affiche résultats
"""

import json
from pathlib import Path
from taest import ProjectAnalyzer


def main():
    print("="*80)
    print("🧪 TEST PROJECTANALYZER - NOMENCLATURE")
    print("="*80)
    
    # Vérifier que main.py existe
    if not Path(r"C:\Users\joxle\Desktop\ai_Pingpong\main.py").exists():
        print("\n❌ ERREUR: main.py introuvable")
        return
    
    print("\n✅ Fichier trouvé: main.py")
    
    # Analyser
    print("\n🔍 Analyse en cours...")
    analyzer = ProjectAnalyzer(".")
    analysis = analyzer.analyze()
    
    # Sauvegarder JSON
    with open("aa.json", 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print("✅ JSON sauvegardé: aa.json")
    
    # Afficher nomenclature
    nomenclature = analysis.get('nomenclature', {})
    
    if not nomenclature:
        print("\n⚠️ ATTENTION: 'nomenclature' absent du JSON")
        print("\nContenu du JSON:")
        print(json.dumps(analysis, indent=2)[:500])
        return
    
    print("\n" + "="*80)
    print("📊 NOMENCLATURE EXTRAITE")
    print("="*80)
    
    # Classes
    classes = nomenclature.get('all_class_names', [])
    print(f"\n📦 CLASSES ({len(classes)}):")
    for cls in classes:
        print(f"   - {cls}")
    
    # Fonctions
    functions = nomenclature.get('all_function_names', [])
    print(f"\n🔧 FONCTIONS GLOBALES ({len(functions)}):")
    for func in functions:
        print(f"   - {func}()")
    
    # Détails première classe
    classes_data = nomenclature.get('classes', {})
    if classes_data:
        first_class = list(classes_data.keys())[0]
        class_data = classes_data[first_class]
        
        print(f"\n" + "="*80)
        print(f"📋 DÉTAILS DE: {first_class}")
        print("="*80)
        
        # Variables d'instance
        inst_vars = class_data.get('instance_variables_by_method', {})
        print(f"\n🔧 Variables d'instance par méthode:")
        if inst_vars:
            for method, vars_list in inst_vars.items():
                print(f"   {method}: {vars_list}")
        else:
            print("   (aucune)")
        
        # Méthodes
        methods = class_data.get('method_names', [])
        print(f"\n📋 Méthodes ({len(methods)}):")
        for method in methods[:10]:  # 10 premières
            print(f"   - {method}()")
        if len(methods) > 10:
            print(f"   ... et {len(methods)-10} autres")
        
        # Variables locales (première méthode)
        local_vars = class_data.get('methods_local_vars', {})
        if local_vars:
            first_method = list(local_vars.keys())[0]
            method_vars = local_vars[first_method]
            
            print(f"\n🔍 Variables locales de {first_method}():")
            print(f"   Paramètres: {method_vars.get('parameters', [])}")
            print(f"   Assigned: {method_vars.get('assigned', [])}")
            print(f"   For loops: {method_vars.get('for_vars', [])}")
            print(f"   With: {method_vars.get('with_vars', [])}")
    
    print("\n" + "="*80)
    print("✅ TEST TERMINÉ")
    print("="*80)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
