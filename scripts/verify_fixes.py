#!/usr/bin/env python3
"""
Verify that all fixes have been applied correctly
"""
import json
import time
from typing import Dict, List, Tuple

import requests

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def check_endpoint(url: str, method: str = "GET", expected_status: int = 200) -> Tuple[bool, str]:
    """Check if endpoint returns expected status"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, timeout=5)
        
        success = response.status_code == expected_status
        message = f"Status: {response.status_code} {'✅' if success else '❌'}"
        return success, message
    except Exception as e:
        return False, f"Error: {str(e)}"

def check_assets() -> Dict[str, any]:
    """Check if all assets are loading correctly"""
    print("\n📁 Checking Assets...")
    print("-" * 50)
    
    assets = [
        "logo_c4ai.png",
        "logo_fapesp.png",
        "logo_ibm.png",
        "logo_usp.png",
        "logo_esalq.png",
        "dashExtensions_default.js"
    ]
    
    results = {}
    for asset in assets:
        url = f"{BASE_URL}/assets/{asset}"
        success, message = check_endpoint(url)
        results[asset] = success
        status = "✅" if success else "❌"
        print(f"{status} {asset:30} - {message}")
    
    return results

def check_dash_layout() -> bool:
    """Check if Dash layout loads without errors"""
    print("\n🎨 Checking Dash Layout...")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/_dash-layout", timeout=5)
        
        if response.status_code != 200:
            print(f"❌ Dash layout status: {response.status_code}")
            return False
        
        # Check if layout contains expected components
        layout_text = response.text
        components = [
            'page-content',
            'navbar',
            'footer',
            'language-toggle'
        ]
        
        for component in components:
            if component in layout_text:
                print(f"✅ Component '{component}' found")
            else:
                print(f"❌ Component '{component}' NOT found")
                return False
        
        print(f"✅ Dash layout loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error loading Dash layout: {e}")
        return False

def check_api_health() -> bool:
    """Check API health"""
    print("\n🏥 Checking API Health...")
    print("-" * 50)
    
    success, message = check_endpoint(f"{API_URL}/health")
    status = "✅" if success else "❌"
    print(f"{status} API Health: {message}")
    return success

def check_home_page() -> bool:
    """Check if home page loads"""
    print("\n🏠 Checking Home Page...")
    print("-" * 50)
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        
        if response.status_code != 200:
            print(f"❌ Home page status: {response.status_code}")
            return False
        
        if "EVAonline" in response.text:
            print(f"✅ Home page contains 'EVAonline'")
        else:
            print(f"❌ Home page doesn't contain 'EVAonline'")
            return False
        
        print(f"✅ Home page loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error loading home page: {e}")
        return False

def main():
    print("=" * 50)
    print("🔍 EVAonline Fixes Verification")
    print("=" * 50)
    
    # Wait for services to be ready
    print("\n⏳ Waiting for services to be ready...")
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/api/health", timeout=2)
            print("✅ Services are ready!")
            break
        except:
            if i < 9:
                print(f"  Attempt {i+1}/10 - waiting...")
                time.sleep(2)
    
    results = {
        "api_health": check_api_health(),
        "home_page": check_home_page(),
        "dash_layout": check_dash_layout(),
        "assets": check_assets(),
    }
    
    print("\n" + "=" * 50)
    print("📊 Summary")
    print("=" * 50)
    
    all_assets_ok = all(results["assets"].values())
    
    print(f"{'✅' if results['api_health'] else '❌'} API Health")
    print(f"{'✅' if results['home_page'] else '❌'} Home Page")
    print(f"{'✅' if results['dash_layout'] else '❌'} Dash Layout")
    print(f"{'✅' if all_assets_ok else '❌'} All Assets ({sum(results['assets'].values())}/{len(results['assets'])} OK)")
    
    success = all(results.values()) and all_assets_ok
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All fixes verified successfully!")
        print("\nNext steps:")
        print("1. Open http://localhost:8000 in browser")
        print("2. Open Developer Console (F12)")
        print("3. Check for any errors in the Console tab")
        print("4. Test interactive features:")
        print("   - Click on the map")
        print("   - Toggle language")
        print("   - Submit ETo calculation")
    else:
        print("❌ Some checks failed. Please review the output above.")
    print("=" * 50)

if __name__ == "__main__":
    main()
