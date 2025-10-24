#!/usr/bin/env python3
"""
PHASE 3.5.4 Pre-test Verification Script

Verifica se todos os componentes estão prontos para o WebSocket E2E Testing.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Tuple

import requests

# Add project root to path - go up 3 levels from scripts/testing/
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

class PreTestVerifier:
    """Verifica pré-condições para PHASE 3.5.4"""
    
    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def check(self, name: str, condition: bool, details: str = "") -> bool:
        """Registra resultado de verificação"""
        status = "✅ PASS" if condition else "❌ FAIL"
        if not condition and details:
            self.results[name] = f"{status}: {details}"
            self.failed += 1
        elif not condition:
            self.results[name] = status
            self.failed += 1
        else:
            self.results[name] = status
            self.passed += 1
        return condition
    
    def warn(self, name: str, details: str = ""):
        """Registra aviso"""
        self.results[name] = f"⚠️ WARNING: {details}"
        self.warnings += 1
    
    def verify_backend(self) -> bool:
        """Verifica se Backend está rodando"""
        print("\n🔍 Checking Backend...")
        try:
            response = requests.get("http://localhost:8000/docs", timeout=2)
            return self.check("Backend Server", response.status_code == 200)
        except Exception as e:
            return self.check("Backend Server", False, str(e))
    
    def verify_frontend(self) -> bool:
        """Verifica se Frontend está rodando"""
        print("🔍 Checking Frontend...")
        try:
            response = requests.get("http://localhost:8050/", timeout=2)
            return self.check("Frontend Server", response.status_code == 200)
        except Exception as e:
            return self.check("Frontend Server", False, str(e))
    
    def verify_redis(self) -> bool:
        """Verifica se Redis está rodando"""
        print("🔍 Checking Redis...")
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
            r.ping()
            return self.check("Redis", True)
        except Exception as e:
            self.warn("Redis", "Redis not reachable or not installed")
            return False
    
    def verify_files(self) -> bool:
        """Verifica arquivos críticos"""
        print("🔍 Checking Files...")
        
        files_to_check = {
            "language_switcher": "frontend/components/language_switcher.py",
            "websocket_handler": "frontend/utils/websocket_handler.py",
            "eto_callbacks": "frontend/callbacks/eto_callbacks.py",
            "en.json": "config/translations/en.json",
            "pt.json": "config/translations/pt.json",
            "get_translations": "utils/get_translations.py",
            "language_manager": "utils/language_manager.py",
        }
        
        all_exist = True
        for name, path in files_to_check.items():
            full_path = project_root / path
            exists = full_path.exists()
            if not exists:
                self.check(f"File: {name}", exists, f"Not found: {path}")
                all_exist = False
            else:
                # Verify file is not empty
                size = full_path.stat().st_size
                if size > 0:
                    self.check(f"File: {name}", True)
                else:
                    self.check(f"File: {name}", False, "File is empty")
                    all_exist = False
        
        return all_exist
    
    def verify_json_syntax(self) -> bool:
        """Verifica sintaxe dos arquivos JSON"""
        print("🔍 Checking JSON Syntax...")
        
        json_files = {
            "pt.json": "config/translations/pt.json",
            "en.json": "config/translations/en.json",
        }
        
        all_valid = True
        for name, path in json_files.items():
            full_path = project_root / path
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    key_count = len(data)
                    self.check(f"JSON: {name}", True)
                    self.results[f"JSON: {name} keys"] = f"✅ {key_count} keys found"
            except json.JSONDecodeError as e:
                self.check(f"JSON: {name}", False, f"Invalid JSON: {e}")
                all_valid = False
            except Exception as e:
                self.check(f"JSON: {name}", False, f"Error: {e}")
                all_valid = False
        
        return all_valid
    
    def verify_python_imports(self) -> bool:
        """Verifica imports Python críticos"""
        print("🔍 Checking Python Imports...")
        
        imports_to_check = {
            "dash": "import dash",
            "dcc": "from dash import dcc",
            "dbc": "import dash_bootstrap_components as dbc",
            "websocket": "from frontend.utils.websocket_handler import WebSocketConnectionManager",
        }
        
        all_importable = True
        for name, import_str in imports_to_check.items():
            try:
                exec(import_str)
                self.check(f"Import: {name}", True)
            except ImportError as e:
                self.warn(f"Import: {name}", f"Not installed or not found")
                all_importable = False
            except Exception as e:
                self.check(f"Import: {name}", False, str(e))
                all_importable = False
        
        return all_importable
    
    def verify_environment(self) -> bool:
        """Verifica variáveis de ambiente"""
        print("🔍 Checking Environment...")
        
        # Verificar se estamos no diretório certo
        app_py = project_root / "frontend" / "app.py"
        if app_py.exists():
            self.check("Project Root", True)
        else:
            self.check("Project Root", False, "frontend/app.py not found")
        
        return app_py.exists()
    
    def run_all_checks(self) -> Tuple[bool, Dict]:
        """Executa todas as verificações"""
        print("\n" + "="*60)
        print("🧪 PHASE 3.5.4 PRE-TEST VERIFICATION")
        print("="*60)
        
        # Run checks
        backend_ok = self.verify_backend()
        frontend_ok = self.verify_frontend()
        redis_ok = self.verify_redis()
        files_ok = self.verify_files()
        json_ok = self.verify_json_syntax()
        imports_ok = self.verify_python_imports()
        env_ok = self.verify_environment()
        
        # Summary
        print("\n" + "="*60)
        print("📊 VERIFICATION SUMMARY")
        print("="*60)
        
        for check_name, status in self.results.items():
            print(f"{check_name:40} {status}")
        
        print(f"\n✅ Passed:  {self.passed}")
        print(f"❌ Failed:  {self.failed}")
        print(f"⚠️  Warnings: {self.warnings}")
        
        # Overall status
        print("\n" + "="*60)
        if self.failed == 0:
            print("✅ ALL CRITICAL CHECKS PASSED")
            print("Ready for WebSocket E2E Testing! 🚀")
            ready = True
        else:
            print("❌ SOME CRITICAL CHECKS FAILED")
            print("Please fix issues before proceeding")
            ready = False
        
        if self.warnings > 0:
            print(f"⚠️  {self.warnings} warning(s) - review above")
        
        print("="*60 + "\n")
        
        return ready, self.results

def main():
    """Main entry point"""
    verifier = PreTestVerifier()
    ready, results = verifier.run_all_checks()
    
    # Return exit code
    sys.exit(0 if ready else 1)

if __name__ == "__main__":
    main()
