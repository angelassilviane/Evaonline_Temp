#!/usr/bin/env python3
"""
Verifica problemas específicos conhecidos.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Main."""
    print("\n" + "="*80)
    print("🔍 VERIFICAÇÃO DE PROBLEMAS ESPECÍFICOS")
    print("="*80 + "\n")
    
    issues_found = []
    project_root = Path(__file__).parent.parent
    
    # ====================================================================
    # 1. Verificar se data_fusion.py ainda existe
    # ====================================================================
    
    data_fusion = project_root / "backend/core/data_processing/data_fusion.py"
    if data_fusion.exists():
        print("🔴 PROBLEMA 1: data_fusion.py ainda existe")
        print("   └─ Deveria ser deletado (substituído por kalman_ensemble.py)")
        print(f"   └─ Arquivo: {data_fusion}\n")
        issues_found.append("data_fusion.py exists")
    else:
        print("✅ PROBLEMA 1: data_fusion.py não existe (OK)\n")
    
    # ====================================================================
    # 2. Verificar se elevation/ ainda existe
    # ====================================================================
    
    elevation = project_root / "backend/core/elevation"
    if elevation.exists():
        print("🔴 PROBLEMA 2: elevation/ pasta ainda existe")
        print("   └─ Deveria ser deletada (redundante)")
        print(f"   └─ Pasta: {elevation}\n")
        issues_found.append("elevation folder exists")
    else:
        print("✅ PROBLEMA 2: elevation/ não existe (OK)\n")
    
    # ====================================================================
    # 3. Verificar imports em data_download.py
    # ====================================================================
    
    data_download = project_root / "backend/core/data_processing/data_download.py"
    if data_download.exists():
        content = data_download.read_text(encoding='utf-8')
        
        has_data_fusion_import = "from backend.core.data_processing.data_fusion import" in content
        has_kalman_import = "from backend.core.data_processing.kalman_ensemble import" in content
        
        if has_data_fusion_import:
            print("🔴 PROBLEMA 3: data_download.py ainda importa data_fusion")
            print("   └─ Deve usar kalman_ensemble.KalmanEnsembleStrategy")
            print("   └─ Remova: from backend.core.data_processing.data_fusion import")
            print("   └─ Adicione: from backend.core.data_processing.kalman_ensemble import KalmanEnsembleStrategy\n")
            issues_found.append("data_download imports data_fusion")
        elif has_kalman_import:
            print("✅ PROBLEMA 3: data_download.py importa kalman_ensemble (OK)\n")
        else:
            print("⚠️  PROBLEMA 3: data_download.py não importa nem data_fusion nem kalman_ensemble")
            print("   └─ Verificar manualmente\n")
            issues_found.append("data_download missing both imports")
    else:
        print("⚠️  PROBLEMA 3: data_download.py não existe")
        print(f"   └─ Arquivo esperado em: {data_download}\n")
    
    # ====================================================================
    # 4. Verificar celery_config.py imports
    # ====================================================================
    
    celery_config = project_root / "backend/infrastructure/celery/celery_config.py"
    if celery_config.exists():
        content = celery_config.read_text(encoding='utf-8')
        
        # Verificar se tem try/except para prometheus_metrics
        has_try_except = "try:" in content and "prometheus_metrics" in content and "except" in content
        
        if not has_try_except:
            print("🟡 PROBLEMA 4: celery_config.py pode ter circular import de prometheus_metrics")
            print("   └─ Deve estar protegido por try/except")
            print("   └─ Verificar linhas que importam CELERY_TASK_DURATION, CELERY_TASKS_TOTAL\n")
            issues_found.append("celery_config missing try/except for prometheus")
        else:
            print("✅ PROBLEMA 4: celery_config.py tem try/except para prometheus_metrics (OK)\n")
    else:
        print("⚠️  PROBLEMA 4: celery_config.py não existe")
        print(f"   └─ Arquivo esperado em: {celery_config}\n")
    
    # ====================================================================
    # 5. Verificar se tasks/ está realmente vazio
    # ====================================================================
    
    tasks_folder = project_root / "backend/infrastructure/celery/tasks"
    if tasks_folder.exists():
        py_files = list(tasks_folder.glob("*.py"))
        py_files = [f for f in py_files if f.name != "__init__.py"]
        
        if len(py_files) > 0:
            print("🟡 PROBLEMA 5: tasks/ tem arquivos que deveriam estar em climate_tasks.py")
            print(f"   └─ Arquivos encontrados: {[f.name for f in py_files]}")
            print("   └─ Mover para backend/infrastructure/cache/climate_tasks.py\n")
            issues_found.append("tasks folder has files")
        else:
            print("✅ PROBLEMA 5: tasks/ está vazio (OK)\n")
    else:
        print("⚠️  PROBLEMA 5: tasks/ não existe")
        print(f"   └─ Pasta esperada em: {tasks_folder}\n")
    
    # ====================================================================
    # 6. Verificar se kalman_ensemble.py existe
    # ====================================================================
    
    kalman_file = project_root / "backend/core/data_processing/kalman_ensemble.py"
    if kalman_file.exists():
        print("✅ PROBLEMA 6: kalman_ensemble.py existe (OK)\n")
    else:
        print("🔴 PROBLEMA 6: kalman_ensemble.py não existe!")
        print("   └─ Arquivo crítico para data fusion\n")
        issues_found.append("kalman_ensemble.py missing")
    
    # ====================================================================
    # 7. Verificar se frontend/assets ainda existe
    # ====================================================================
    
    frontend_assets = project_root / "frontend/assets"
    if frontend_assets.exists():
        print("🟡 PROBLEMA 7: frontend/assets/ ainda existe")
        print("   └─ Assets deveriam estar em raiz/assets/")
        print("   └─ Se estiver vazio, pode ser deletado\n")
        issues_found.append("frontend/assets still exists")
    else:
        print("✅ PROBLEMA 7: frontend/assets/ não existe (OK)\n")
    
    # ====================================================================
    # 8. Verificar se assets está na raiz
    # ====================================================================
    
    assets_root = project_root / "assets"
    if assets_root.exists():
        print("✅ PROBLEMA 8: assets/ está na raiz (OK)")
        
        # Check for critical folders
        has_css = (assets_root / "css").exists()
        has_js = (assets_root / "js").exists()
        has_images = (assets_root / "images").exists()
        
        print(f"   ├─ css/: {'✅' if has_css else '❌'}")
        print(f"   ├─ js/: {'✅' if has_js else '❌'}")
        print(f"   └─ images/: {'✅' if has_images else '❌'}\n")
        
        if not (has_css and has_js and has_images):
            issues_found.append("assets subfolder missing")
    else:
        print("🔴 PROBLEMA 8: assets/ não está na raiz!")
        print("   └─ Esperado em: {assets_root}\n")
        issues_found.append("assets not at root")
    
    # ====================================================================
    # RESUMO
    # ====================================================================
    
    print("="*80)
    if issues_found:
        print(f"🔴 PROBLEMAS ENCONTRADOS: {len(issues_found)}")
        for issue in issues_found:
            print(f"   - {issue}")
        print("\nRECOMENDAÇÃO: Resolver problemas acima antes de PHASE 3.5.4")
    else:
        print("✅ NENHUM PROBLEMA ESPECÍFICO ENCONTRADO")
        print("\nPROJETO PRONTO PARA PHASE 3.5.4!")
    
    print("="*80 + "\n")
    
    return len(issues_found) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
