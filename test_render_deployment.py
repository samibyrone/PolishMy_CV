#!/usr/bin/env python3
"""
Comprehensive test script for CVLatex deployment on Render
"""

import requests
import json
import sys
import time

def test_deployment(base_url):
    """Test deployment with comprehensive diagnostics"""
    print(f"🔍 Testing deployment at: {base_url}")
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    try:
        # Test basic connectivity
        print("\n🌐 Testing basic connectivity...")
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ App is responding")
        else:
            print(f"⚠️ App responded with status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect: {e}")
        return False
    
    # Test comprehensive system diagnostics
    print("\n🔧 Running comprehensive system diagnostics...")
    try:
        response = requests.get(f"{base_url}/debug/test-latex-comprehensive", timeout=30)
        if response.status_code == 200:
            debug_data = response.json()
            
            print(f"📅 Timestamp: {debug_data.get('timestamp', 'unknown')}")
            print(f"📱 Platform: {debug_data.get('system', {}).get('platform', 'unknown')}")
            print(f"🐍 Python: {debug_data.get('system', {}).get('python_version', 'unknown')}")
            print(f"👤 User: {debug_data.get('system', {}).get('user', 'unknown')}")
            print(f"📁 Working Dir: {debug_data.get('system', {}).get('current_dir', 'unknown')}")
            print(f"💾 Disk Space: {debug_data.get('disk_space', 'unknown')}")
            
            # Environment info
            env = debug_data.get('environment', {})
            print(f"🌐 Render Environment: {env.get('render', 'Not detected')}")
            print(f"🔧 Debian Frontend: {env.get('debian_frontend', 'Not set')}")
            
            # Directory info
            dirs = debug_data.get('directories', {})
            print(f"📂 Output exists: {'✅' if dirs.get('output_exists') else '❌'}")
            print(f"📂 Upload exists: {'✅' if dirs.get('upload_exists') else '❌'}")
            print(f"📂 /tmp writable: {'✅' if dirs.get('tmp_writable') else '❌'}")
            
            # LaTeX info
            latex = debug_data.get('latex', {})
            print(f"📝 LaTeX available: {'✅' if latex.get('available_global') else '❌'}")
            print(f"📍 pdflatex path: {latex.get('pdflatex_path', 'Not found')}")
            
            # Found binaries
            binaries = latex.get('found_binaries', [])
            if binaries:
                print(f"🔍 Found LaTeX binaries ({len(binaries)}):")
                for binary in binaries[:5]:  # Show first 5
                    print(f"   - {binary}")
                if len(binaries) > 5:
                    print(f"   ... and {len(binaries) - 5} more")
            else:
                print("🔍 No LaTeX binaries found")
            
            # Package info
            packages = debug_data.get('packages', {})
            print("📦 Package status:")
            for package, status in packages.items():
                status_icon = "✅" if status == "installed" else "❌" if status == "not_installed" else "❓"
                print(f"   {status_icon} {package}: {status}")
            
            # Compilation test
            comp_test = latex.get('compilation_test', {})
            if comp_test.get('status') == 'success':
                print(f"🧪 LaTeX compilation test: ✅ Success (PDF: {comp_test.get('pdf_size', 0)} bytes)")
            elif comp_test.get('status') == 'failed':
                print(f"🧪 LaTeX compilation test: ❌ Failed (Return code: {comp_test.get('return_code', 'unknown')})")
                if comp_test.get('stderr_preview'):
                    print(f"   Error preview: {comp_test.get('stderr_preview', '')}")
            elif comp_test.get('status') == 'skipped':
                print(f"🧪 LaTeX compilation test: ⏭️ Skipped ({comp_test.get('reason', 'unknown')})")
            else:
                print(f"🧪 LaTeX compilation test: ❓ Unknown status: {comp_test.get('status', 'unknown')}")
            
            # Build files
            build_files = debug_data.get('files', {}).get('build_files', [])
            if build_files:
                print(f"📄 Build files found: {', '.join(build_files)}")
            
            latex_warning = debug_data.get('files', {}).get('latex_warning_exists', False)
            if latex_warning:
                print("⚠️ LaTeX warning file exists")
                
        else:
            print(f"❌ Comprehensive diagnostics failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Diagnostics request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse diagnostics response: {e}")
    
    # Test Create CV functionality
    print("\n👤 Testing Create CV API...")
    test_cv_data = {
        "personal_info": {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890",
            "location": "Test City"
        },
        "education": [{
            "degree": "Test Degree",
            "institution": "Test University",
            "year": "2023",
            "description": "Test education description"
        }],
        "experience": [{
            "title": "Test Position",
            "company": "Test Company",
            "duration": "2023-Present",
            "description": "Test work experience description"
        }],
        "skills": ["Python", "LaTeX", "Testing"],
        "projects": [],
        "custom_sections": []
    }
    
    try:
        response = requests.post(f"{base_url}/api/create-cv", json=test_cv_data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            print("✅ Create CV API successful!")
            print(f"📄 LaTeX file: {result.get('latex_file', 'Not provided')}")
            print(f"📄 PDF file: {result.get('pdf_file', 'None - PDF compilation failed')}")
            print(f"📝 LaTeX available: {result.get('latex_available', 'unknown')}")
            
            if result.get('warning'):
                print(f"⚠️ Warning: {result.get('warning')}")
            
            # Test file downloads
            latex_file = result.get('latex_file')
            pdf_file = result.get('pdf_file')
            
            if latex_file:
                try:
                    latex_response = requests.get(f"{base_url}/download/{latex_file}", timeout=10)
                    print(f"📥 LaTeX download: {latex_response.status_code} ({len(latex_response.content)} bytes)")
                except Exception as e:
                    print(f"❌ LaTeX download failed: {e}")
            
            if pdf_file:
                try:
                    pdf_response = requests.get(f"{base_url}/download/{pdf_file}", timeout=10)
                    print(f"📥 PDF download: {pdf_response.status_code} ({len(pdf_response.content)} bytes)")
                except Exception as e:
                    print(f"❌ PDF download failed: {e}")
            else:
                print("📥 PDF download: Skipped (no PDF file)")
                
        else:
            print(f"❌ Create CV API failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Create CV request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse Create CV response: {e}")
    
    print("\n🎯 Diagnosis complete!")
    
    # Provide recommendations
    print("\n💡 Recommendations:")
    
    # Check if we have latex info from diagnostics
    latex_available = False
    if 'debug_data' in locals() and debug_data:
        latex = debug_data.get('latex', {})
        latex_available = latex.get('available_global', False)
    
    if not latex_available:
        print("❌ LaTeX is not installed or not working properly")
        print("   📋 Possible solutions:")
        print("   1. Check if the build script ran successfully during deployment")
        print("   2. Try redeploying to trigger a fresh build")
        print("   3. Consider using a VPS with manual LaTeX installation")
        print("   4. Use the LaTeX source download feature as a workaround")
    else:
        print("✅ LaTeX appears to be working correctly")
    
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_render_deployment.py <base_url>")
        print("Example: python test_render_deployment.py https://cvlatex.onrender.com")
        sys.exit(1)
    
    base_url = sys.argv[1]
    test_deployment(base_url)

if __name__ == "__main__":
    main() 