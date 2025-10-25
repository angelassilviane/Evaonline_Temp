#!/usr/bin/env python3
"""
AUDITORIA COMPLETA DO PROJETO EVAonline
Verifica TUDO: imports, configurações, integrações, etc.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

class ComprehensiveAudit:
    """Auditoria completa do projeto."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.issues = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_failed = 0
    
    def print_section(self, title: str):
        """Print formatted section."""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    
    def check(self, name: str, condition: bool, details: str = ""):
        """Register check result."""
        if condition:
            print(f"✅ {name}")
            self.checks_passed += 1
        else:
            status = f"❌ {name}"
            if details:
                status += f"\n   └─ {details}"
            print(status)
            self.issues.append((name, details))
            self.checks_failed += 1
    
    def warn(self, name: str, details: str = ""):
        """Register warning."""
        print(f"⚠️  {name}")
        if details:
            print(f"   └─ {details}")
        self.warnings.append((name, details))
    
    # ========================================================================
    # 1. VERIFICAR ESTRUTURA DE ARQUIVOS
    # ========================================================================
    
    def audit_file_structure(self) -> bool:
        """Audit critical files exist."""
        self.print_section("1️⃣ ESTRUTURA DE ARQUIVOS")
        
        critical_files = {
            "Backend": [
                "backend/main.py",
                "backend/database/connection.py",
                "backend/database/models.py",
                "backend/api/routes/__init__.py",
                "backend/core/eto_calculation/eto_calculation.py",
            ],
            "Frontend": [
                "frontend/app.py",
                "frontend/callbacks/eto_callbacks.py",
                "frontend/components/navbar.py",
                "frontend/components/footer.py",
                "frontend/pages/home.py",
            ],
            "Config": [
                "config/settings/app_settings.py",
                "config/translations/pt.json",
                "config/translations/en.json",
            ],
            "Docker": [
                "Dockerfile",
                "docker-compose.yml",
                "entrypoint.sh",
            ],
            "Requirements": [
                "requirements/base.txt",
                "requirements/production.txt",
            ]
        }
        
        all_exist = True
        for category, files in critical_files.items():
            print(f"\n{category}:")
            for file_path in files:
                full_path = self.project_root / file_path
                exists = full_path.exists()
                self.check(f"  {file_path}", exists)
                if not exists:
                    all_exist = False
        
        return all_exist
    
    # ========================================================================
    # 2. VERIFICAR ASSETS
    # ========================================================================
    
    def audit_assets(self) -> bool:
        """Audit assets structure."""
        self.print_section("2️⃣ VERIFICAÇÃO DE ASSETS")
        
        assets_root = self.project_root / "assets"
        
        # Check main folder
        self.check("Pasta assets na raiz", assets_root.exists())
        
        # Check subfolders
        subfolders = {
            "css": assets_root / "css",
            "js": assets_root / "js",
            "images": assets_root / "images",
        }
        
        all_ok = True
        for folder_name, folder_path in subfolders.items():
            exists = folder_path.exists()
            self.check(f"  assets/{folder_name}/", exists)
            if not exists:
                all_ok = False
        
        # Check critical image files
        if (assets_root / "images").exists():
            images = {
                "logo_c4ai.png": "C4AI",
                "logo_fapesp.png": "FAPESP",
                "logo_ibm.png": "IBM",
                "logo_usp.png": "USP",
                "logo_esalq.png": "ESALQ",
            }
            
            print("\n  Imagens:")
            for image_file, partner_name in images.items():
                path = assets_root / "images" / image_file
                exists = path.exists()
                self.check(f"    {image_file}", exists)
                if not exists:
                    all_ok = False
        
        return all_ok
    
    # ========================================================================
    # 3. VERIFICAR CONFIGURAÇÕES
    # ========================================================================
    
    def audit_settings(self) -> bool:
        """Audit app settings."""
        self.print_section("3️⃣ VERIFICAÇÃO DE CONFIGURAÇÕES")
        
        try:
            from config.settings import get_settings
            settings = get_settings()
            
            # Verificar variáveis críticas
            critical_vars = [
                ("PROJECT_NAME", settings.PROJECT_NAME),
                ("API_V1_PREFIX", settings.API_V1_PREFIX),
                ("DASH_ASSETS_FOLDER", settings.DASH_ASSETS_FOLDER),
            ]
            
            all_set = True
            for var_name, var_value in critical_vars:
                has_value = var_value and str(var_value).strip() != ""
                details = str(var_value)[:60] if has_value else "VAZIO"
                self.check(f"  {var_name}", has_value, details)
                if not has_value:
                    all_set = False
            
            # Verificar se DASH_ASSETS_FOLDER aponta para a raiz
            assets_folder = str(settings.DASH_ASSETS_FOLDER)
            is_correct_path = "assets" in assets_folder and "frontend" not in assets_folder
            self.check(
                "  DASH_ASSETS_FOLDER aponta para raiz/assets",
                is_correct_path,
                f"Caminho: {assets_folder}"
            )
            
            return all_set and is_correct_path
            
        except Exception as e:
            self.check("Load Settings", False, str(e))
            return False
    
    # ========================================================================
    # 4. VERIFICAR IMPORTS CRÍTICOS
    # ========================================================================
    
    def audit_imports(self) -> bool:
        """Audit Python imports for issues."""
        self.print_section("4️⃣ VERIFICAÇÃO DE IMPORTS")
        
        critical_imports = [
            ("Config Settings", "from config.settings import get_settings"),
            ("FastAPI", "from fastapi import FastAPI"),
            ("Dash", "import dash"),
            ("SQLAlchemy", "from sqlalchemy import create_engine"),
            ("Pandas", "import pandas as pd"),
        ]
        
        all_ok = True
        for name, import_str in critical_imports:
            try:
                exec(import_str)
                self.check(f"  {name}", True)
            except ImportError as e:
                self.check(f"  {name}", False, str(e))
                all_ok = False
            except Exception as e:
                self.check(f"  {name}", False, f"Erro: {e}")
                all_ok = False
        
        return all_ok
    
    # ========================================================================
    # 5. VERIFICAR ARQUIVOS OBSOLETOS
    # ========================================================================
    
    def audit_obsolete_files(self) -> bool:
        """Audit for obsolete files that should be deleted."""
        self.print_section("5️⃣ VERIFICAÇÃO DE ARQUIVOS OBSOLETOS")
        
        obsolete_files = {
            "data_fusion.py": self.project_root / "backend/core/data_processing/data_fusion.py",
            "elevation/": self.project_root / "backend/core/elevation",
        }
        
        all_clean = True
        for file_name, file_path in obsolete_files.items():
            exists = file_path.exists()
            if exists:
                self.warn(
                    f"Arquivo obsoleto encontrado: {file_name}",
                    f"Deveria ser deletado: {file_path}"
                )
                all_clean = False
            else:
                self.check(f"  {file_name} não existe", True)
        
        return all_clean
    
    # ========================================================================
    # 6. VERIFICAR FRONTEND APP.PY
    # ========================================================================
    
    def audit_frontend_app(self) -> bool:
        """Audit frontend/app.py configuration."""
        self.print_section("6️⃣ VERIFICAÇÃO DE FRONTEND/APP.PY")
        
        app_file = self.project_root / "frontend/app.py"
        
        if not app_file.exists():
            self.check("frontend/app.py existe", False)
            return False
        
        self.check("frontend/app.py existe", True)
        
        content = app_file.read_text(encoding='utf-8')
        
        # Check for key components
        checks = {
            "create_dash_app() function": "def create_dash_app" in content,
            "assets_folder parameter": "assets_folder=" in content,
            "Callback registrations": "register_" in content,
            "Language store": "language-store" in content,
        }
        
        all_ok = True
        for check_name, has_component in checks.items():
            self.check(f"  {check_name}", has_component)
            if not has_component:
                all_ok = False
        
        return all_ok
    
    # ========================================================================
    # 7. VERIFICAR TRADUCOES
    # ========================================================================
    
    def audit_translations(self) -> bool:
        """Audit translation files."""
        self.print_section("7️⃣ VERIFICAÇÃO DE TRADUÇÕES")
        
        translation_files = {
            "Portuguese": self.project_root / "config/translations/pt.json",
            "English": self.project_root / "config/translations/en.json",
        }
        
        all_valid = True
        for lang, file_path in translation_files.items():
            if not file_path.exists():
                self.check(f"  {lang} translation", False, "Arquivo não encontrado")
                all_valid = False
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    key_count = len(data)
                    self.check(f"  {lang} translation", True, f"{key_count} chaves")
            except json.JSONDecodeError as e:
                self.check(f"  {lang} translation", False, f"JSON inválido: {e}")
                all_valid = False
            except Exception as e:
                self.check(f"  {lang} translation", False, str(e))
                all_valid = False
        
        return all_valid
    
    # ========================================================================
    # 8. VERIFICAR DOCKER
    # ========================================================================
    
    def audit_docker(self) -> bool:
        """Audit Docker configuration."""
        self.print_section("8️⃣ VERIFICAÇÃO DE DOCKER")
        
        docker_files = {
            "Dockerfile": self.project_root / "Dockerfile",
            "docker-compose.yml": self.project_root / "docker-compose.yml",
            "entrypoint.sh": self.project_root / "entrypoint.sh",
        }
        
        all_exist = True
        for file_name, file_path in docker_files.items():
            exists = file_path.exists()
            self.check(f"  {file_name}", exists)
            if not exists:
                all_exist = False
        
        # Check docker-compose services and volumes
        compose_file = docker_files["docker-compose.yml"]
        if compose_file.exists():
            content = compose_file.read_text(encoding='utf-8')
            
            # Check for assets volume
            has_assets_volume = "./assets:/app/assets" in content
            self.check(
                "  Volume ./assets:/app/assets mapeado",
                has_assets_volume,
                "Necessário para servir assets" if not has_assets_volume else ""
            )
            
            # Check services
            services = {
                "PostgreSQL": "postgres:" in content,
                "Redis": "redis:" in content,
                "Backend": "evaonline-api" in content or "api:" in content,
            }
            
            print("\n  Serviços:")
            for service_name, has_service in services.items():
                self.check(f"    {service_name}", has_service)
                if not has_service:
                    all_exist = False
        
        return all_exist
    
    # ========================================================================
    # 9. VERIFICAR COMPONENTES FRONTEND
    # ========================================================================
    
    def audit_frontend_components(self) -> bool:
        """Audit frontend components."""
        self.print_section("9️⃣ VERIFICAÇÃO DE COMPONENTES FRONTEND")
        
        components = {
            "footer.py": self.project_root / "frontend/components/footer.py",
            "navbar.py": self.project_root / "frontend/components/navbar.py",
            "eto_callbacks.py": self.project_root / "frontend/callbacks/eto_callbacks.py",
            "map_callbacks.py": self.project_root / "frontend/callbacks/map_callbacks.py",
        }
        
        all_exist = True
        for component_name, file_path in components.items():
            exists = file_path.exists()
            self.check(f"  {component_name}", exists)
            if not exists:
                all_exist = False
        
        return all_exist
    
    # ========================================================================
    # 10. VERIFICAR PATHS E REFERÊNCIAS
    # ========================================================================
    
    def audit_paths_and_refs(self) -> bool:
        """Audit asset paths and references."""
        self.print_section("🔟 VERIFICAÇÃO DE PATHS E REFERÊNCIAS")
        
        # Check footer.py for correct asset paths
        footer_file = self.project_root / "frontend/components/footer.py"
        if footer_file.exists():
            content = footer_file.read_text(encoding='utf-8')
            
            # Should have /assets/images paths
            has_correct_path = '/assets/images/logo_' in content
            has_old_path = 'frontend/assets' in content
            
            self.check(
                "  footer.py usa /assets/images/",
                has_correct_path,
                "Caminho correto para imagens"
            )
            
            if has_old_path:
                self.warn(
                    "footer.py pode estar usando caminho antigo",
                    "Verificar se há referências a 'frontend/assets'"
                )
        
        # Check app.py for correct asset stylesheet paths
        app_file = self.project_root / "frontend/app.py"
        if app_file.exists():
            content = app_file.read_text(encoding='utf-8')
            
            # Should reference /assets/css/styles.css, not frontend/assets
            has_correct_css = "'/assets/css/styles.css'" in content or '"/assets/css/styles.css"' in content
            has_old_css = "frontend/assets/styles" in content
            
            self.check(
                "  app.py usa /assets/css/styles.css",
                has_correct_css,
                "Caminho correto para CSS"
            )
            
            if has_old_css:
                self.warn(
                    "app.py pode estar usando caminho antigo de CSS",
                    "Verificar referências a 'frontend/assets/styles'"
                )
        
        return has_correct_path if footer_file.exists() else True
    
    # ========================================================================
    # EXECUTAR AUDITORIA COMPLETA
    # ========================================================================
    
    def run_all_audits(self):
        """Run all audits."""
        print("\n" + "="*80)
        print("🔍 AUDITORIA COMPLETA DO PROJETO EVAONLINE")
        print("="*80)
        
        results = {
            "File Structure": self.audit_file_structure(),
            "Assets": self.audit_assets(),
            "Settings": self.audit_settings(),
            "Imports": self.audit_imports(),
            "Obsolete Files": self.audit_obsolete_files(),
            "Frontend App": self.audit_frontend_app(),
            "Translations": self.audit_translations(),
            "Docker": self.audit_docker(),
            "Frontend Components": self.audit_frontend_components(),
            "Paths & References": self.audit_paths_and_refs(),
        }
        
        # Print summary
        self.print_section("📋 RESUMO FINAL")
        
        print(f"Total Checks: {self.checks_passed + self.checks_failed}")
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.issues:
            print(f"\n🔴 ISSUES ({len(self.issues)}):")
            for issue_name, details in self.issues:
                print(f"   - {issue_name}")
                if details:
                    print(f"     └─ {details}")
        
        if self.warnings:
            print(f"\n🟡 WARNINGS ({len(self.warnings)}):")
            for warning_name, details in self.warnings:
                print(f"   - {warning_name}")
                if details:
                    print(f"     └─ {details}")
        
        # Overall status
        print("\n" + "="*80)
        if self.checks_failed == 0:
            print("✅ TODOS OS CHECKS PASSARAM!")
        elif self.checks_failed <= 3:
            print("🟡 ALGUNS PROBLEMAS ENCONTRADOS - REVISAR ACIMA")
        else:
            print("❌ VÁRIOS PROBLEMAS ENCONTRADOS - AÇÃO NECESSÁRIA")
        print("="*80 + "\n")
        
        return self.checks_failed == 0


def main():
    """Main entry point."""
    audit = ComprehensiveAudit()
    success = audit.run_all_audits()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
