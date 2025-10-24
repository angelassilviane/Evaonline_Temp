#!/usr/bin/env python3
"""
PHASE 3.5.4: Quick Pre-test Verification

Verifica rapidamente se os componentes estão prontos para testing.
"""

import json
from pathlib import Path


def verify():
    """Execute quick verification"""
    print("\n" + "="*70)
    print("🧪 PHASE 3.5.4: PRE-TEST VERIFICATION")
    print("="*70)
    
    root = Path.cwd()
    checks = []
    
    # Check files exist
    files_to_check = {
        "language_switcher.py": root / "frontend" / "components" / "language_switcher.py",
        "websocket_client.py": root / "utils" / "websocket_client.py",
        "language_manager.py": root / "utils" / "language_manager.py",
        "get_translations.py": root / "utils" / "get_translations.py",
        "app.py": root / "frontend" / "app.py",
        "navbar.py": root / "frontend" / "components" / "navbar.py",
        "progress_card.py": root / "frontend" / "components" / "progress_card.py",
        "eto_callbacks.py": root / "frontend" / "callbacks" / "eto_callbacks.py",
        "en.json": root / "config" / "translations" / "en.json",
        "pt.json": root / "config" / "translations" / "pt.json",
    }
    
    print("\n📁 Checking Files:")
    print("-" * 70)
    
    for name, path in files_to_check.items():
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ {name:25} ({size:,} bytes)")
            checks.append(True)
        else:
            print(f"  ❌ {name:25} NOT FOUND")
            checks.append(False)
    
    # Check JSON validity
    print("\n📋 Checking JSON Files:")
    print("-" * 70)
    
    for name, path in [("pt.json", root / "config" / "translations" / "pt.json"),
                        ("en.json", root / "config" / "translations" / "en.json")]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                key_count = len(data)
                print(f"  ✅ {name:25} ({key_count} translation keys)")
                checks.append(True)
        except json.JSONDecodeError as e:
            print(f"  ❌ {name:25} INVALID JSON: {e}")
            checks.append(False)
        except Exception as e:
            print(f"  ❌ {name:25} ERROR: {e}")
            checks.append(False)
    
    # Check imports
    print("\n📦 Checking Python Imports:")
    print("-" * 70)
    
    imports = [
        ("dash", "import dash"),
        ("dash.dcc", "from dash import dcc"),
        ("dash_bootstrap_components", "import dash_bootstrap_components as dbc"),
        ("loguru", "from loguru import logger"),
        ("websockets", "import websockets"),
    ]
    
    for name, import_str in imports:
        try:
            exec(import_str)
            print(f"  ✅ {name:25} available")
            checks.append(True)
        except ImportError:
            print(f"  ⚠️  {name:25} not installed (optional)")
        except Exception as e:
            print(f"  ❌ {name:25} ERROR: {e}")
            checks.append(False)
    
    # Summary
    print("\n" + "="*70)
    passed = sum(1 for c in checks if c)
    total = len(checks)
    
    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("\n🚀 Ready for WebSocket E2E Testing!")
        print("="*70 + "\n")
        return True
    else:
        print(f"⚠️  SOME CHECKS FAILED ({passed}/{total})")
        print("\n❌ Please fix issues before testing")
        print("="*70 + "\n")
        return False

if __name__ == "__main__":
    import sys
    success = verify()
    sys.exit(0 if success else 1)
