import requests
import json
import sys

def test_render_deployment(base_url):
    """Test the Render deployment to diagnose PDF issues"""
    
    print(f"🔍 Testing deployment at: {base_url}")
    
    # Test 1: Check if the app is responding
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ App is responding")
        else:
            print(f"❌ App returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Could not connect to app: {e}")
        return False
    
    # Test 2: Check system configuration
    try:
        print("\n🔧 Checking system configuration...")
        response = requests.get(f"{base_url}/debug/system", timeout=10)
        if response.status_code == 200:
            debug_info = response.json()
            print(f"📱 Platform: {debug_info.get('platform', 'Unknown')}")
            print(f"🐍 Python: {debug_info.get('python_version', 'Unknown')}")
            print(f"📁 Output folder: {debug_info.get('output_folder', 'Unknown')}")
            print(f"📂 Output exists: {debug_info.get('directories', {}).get('output_exists', 'Unknown')}")
            
            latex_info = debug_info.get('latex', {})
            print(f"📝 LaTeX found: {latex_info.get('pdflatex_found', False)}")
            print(f"📍 LaTeX path: {latex_info.get('pdflatex_path', 'Not found')}")
            
            if latex_info.get('version_check'):
                version = latex_info['version_check']
                print(f"🔍 LaTeX version check: return code {version.get('returncode', 'Unknown')}")
                if version.get('stdout'):
                    print(f"📄 LaTeX version: {version['stdout'][:100]}...")
        else:
            print(f"❌ Debug endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ System check failed: {e}")
    
    # Test 3: Test LaTeX compilation
    try:
        print("\n📝 Testing LaTeX compilation...")
        response = requests.get(f"{base_url}/debug/test-latex", timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('compilation_success'):
                print("✅ LaTeX compilation successful!")
                print(f"📄 Test file: {result.get('test_filename')}")
                print(f"📊 File size: {result.get('file_size', 'Unknown')} bytes")
                
                # Test download
                if result.get('download_url'):
                    download_response = requests.get(f"{base_url}{result['download_url']}")
                    if download_response.status_code == 200:
                        print("✅ PDF download successful!")
                    else:
                        print(f"❌ PDF download failed: {download_response.status_code}")
            else:
                print("❌ LaTeX compilation failed")
                if result.get('error'):
                    print(f"🔍 Error: {result['error']}")
        else:
            print(f"❌ LaTeX test endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ LaTeX test failed: {e}")
    
    # Test 4: Test Create CV API
    try:
        print("\n👤 Testing Create CV API...")
        
        test_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1 234 567 8900",
            "summary": "Test summary for deployment verification",
            "education": [{
                "degree": "Test Degree",
                "institution": "Test University",
                "date": "2020-2024"
            }],
            "experience": [{
                "title": "Test Engineer",
                "company": "Test Company", 
                "date": "2024-Present",
                "description": "Testing deployment functionality"
            }]
        }
        
        response = requests.post(f"{base_url}/api/create-cv", 
                               json=test_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Create CV API successful!")
                print(f"📄 LaTeX file: {result.get('latex_file')}")
                print(f"📄 PDF file: {result.get('pdf_file')}")
                
                # Test file downloads
                if result.get('latex_file'):
                    latex_response = requests.get(f"{base_url}/download/{result['latex_file']}")
                    print(f"📥 LaTeX download: {latex_response.status_code}")
                
                if result.get('pdf_file'):
                    pdf_response = requests.get(f"{base_url}/download/{result['pdf_file']}")
                    print(f"📥 PDF download: {pdf_response.status_code}")
                    
                    preview_response = requests.get(f"{base_url}/preview/{result['pdf_file']}")
                    print(f"👁️  PDF preview: {preview_response.status_code}")
                
            else:
                print(f"❌ Create CV failed: {result.get('error')}")
        else:
            print(f"❌ Create CV API failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Create CV test failed: {e}")
    
    print("\n🎯 Diagnosis complete!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_render_deployment.py <render_url>")
        print("Example: python test_render_deployment.py https://your-app.onrender.com")
        sys.exit(1)
    
    render_url = sys.argv[1].rstrip('/')
    test_render_deployment(render_url) 