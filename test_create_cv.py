import requests
import json

# Test data for create CV
test_data = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1 (555) 123-4567",
    "address": "San Francisco, CA",
    "linkedin": "https://linkedin.com/in/johndoe",
    "github": "https://github.com/johndoe",
    "website": "https://johndoe.com",
    "summary": "Passionate software engineer with 5+ years of experience in full-stack development, specializing in modern web technologies and cloud architecture.",
    "education": [
        {
            "degree": "Bachelor of Science in Computer Science",
            "institution": "Stanford University",
            "date": "2018 - 2022",
            "location": "Stanford, CA",
            "gpa": "3.8/4.0",
            "details": "Relevant coursework: Data Structures, Algorithms, Software Engineering, Machine Learning"
        }
    ],
    "experience": [
        {
            "title": "Senior Software Engineer",
            "company": "Google",
            "date": "Jan 2022 - Present",
            "location": "Mountain View, CA",
            "description": "• Led a team of 5 developers in building scalable web applications\n• Improved system performance by 40% through optimization\n• Mentored junior developers and conducted code reviews"
        }
    ],
    "projects": [
        {
            "title": "E-Commerce Platform",
            "description": "Built a full-stack e-commerce platform with user authentication, payment processing, and admin dashboard",
            "technologies": "React, Node.js, MongoDB, Stripe API",
            "date": "2023",
            "link": "https://github.com/johndoe/ecommerce"
        }
    ],
    "skills": {
        "languages": "Python, JavaScript, Java, C++",
        "frameworks": "React, Django, Express.js, TensorFlow",
        "tools": "Git, Docker, AWS, Visual Studio Code",
        "databases": "MySQL, MongoDB, PostgreSQL, Redis",
        "other": "Machine Learning, Data Analysis, Project Management"
    },
    "custom": [
        {
            "title": "Certifications",
            "content": "• AWS Certified Solutions Architect\n• Google Cloud Professional Developer\n• Certified Scrum Master"
        }
    ]
}

def test_create_cv():
    url = "http://localhost:5000/api/create-cv"
    
    try:
        print("Sending request to create CV...")
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ CV Creation successful!")
                print(f"LaTeX file: {result.get('latex_file')}")
                print(f"PDF file: {result.get('pdf_file')}")
                
                # Test file access
                if result.get('latex_file'):
                    latex_url = f"http://localhost:5000/download/{result['latex_file']}"
                    latex_response = requests.get(latex_url)
                    print(f"LaTeX download status: {latex_response.status_code}")
                
                if result.get('pdf_file'):
                    pdf_url = f"http://localhost:5000/download/{result['pdf_file']}"
                    pdf_response = requests.get(pdf_url)
                    print(f"PDF download status: {pdf_response.status_code}")
                    
                    preview_url = f"http://localhost:5000/preview/{result['pdf_file']}"
                    preview_response = requests.get(preview_url)
                    print(f"PDF preview status: {preview_response.status_code}")
                
                # Generate result URL
                result_url = f"http://localhost:5000/result?latex_file={result.get('latex_file')}&pdf_file={result.get('pdf_file')}"
                print(f"Result URL: {result_url}")
                
            else:
                print(f"❌ CV Creation failed: {result.get('error')}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Flask is running on localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_create_cv() 