import os
import re
import json
import requests
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document
import openai
from dotenv import load_dotenv
import tempfile
import subprocess

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# API keys
openai.api_key = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyC5rY2zgtv6x2JM8Ew0Ia-1oCUax2q1ubU')

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
    return text

def enhance_parsing_with_gemini(text):
    """Use Gemini AI to parse CV text and extract structured information"""
    
    prompt = f"""
    Parse the following CV/Resume text and extract structured information in JSON format. 
    IMPORTANT: Only include information that actually exists in the CV text. Do not add placeholder or example data.
    If a field doesn't exist in the CV, either omit it entirely or set it to null/empty.
    
    Required JSON structure (only include fields that have actual data):
    {{
        "name": "Full name (only if found)",
        "email": "Email address (only if found)",
        "phone": "Phone number (only if found)",
        "linkedin": "LinkedIn URL (only if found)",
        "github": "GitHub URL (only if found)",
        "website": "Personal website (only if found)",
        "address": "Address/Location (only if found)",
        "education": [
            {{
                "degree": "Degree name",
                "institution": "Institution name",
                "date": "Date range",
                "location": "Location (if mentioned)",
                "gpa": "GPA (if mentioned)",
                "details": "Additional details (if any)"
            }}
        ],
        "experience": [
            {{
                "title": "Job title",
                "company": "Company name",
                "date": "Date range",
                "location": "Location (if mentioned)",
                "description": ["List of responsibilities and achievements"]
            }}
        ],
        "projects": [
            {{
                "title": "Project name",
                "description": "Project description",
                "technologies": "Technologies used",
                "date": "Date or duration (if mentioned)",
                "link": "Project link (if mentioned)"
            }}
        ],
        "skills": {{
            "languages": ["Programming languages (only if mentioned)"],
            "frameworks": ["Frameworks and libraries (only if mentioned)"],
            "tools": ["Tools and software (only if mentioned)"],
            "libraries": ["Additional libraries (only if mentioned)"],
            "databases": ["Databases (only if mentioned)"],
            "other": ["Other technical skills (only if mentioned)"]
        }},
        "certifications": [
            {{
                "name": "Certification name",
                "issuer": "Issuing organization",
                "date": "Date obtained (if mentioned)"
            }}
        ],
        "awards": ["Awards and honors (only if mentioned)"],
        "languages": ["Spoken languages (only if mentioned)"]
    }}
    
    CV Text:
    {text}
    
    Return only the JSON object with actual data from the CV, no additional text:
    """
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            # Extract the text from Gemini response
            generated_text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Clean the response to extract JSON
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_text = generated_text[json_start:json_end]
                parsed_data = json.loads(json_text)
                return parsed_data
            else:
                print("Failed to extract JSON from Gemini response")
                return None
        else:
            print(f"Gemini API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return None

def parse_cv_text(text):
    """Parse CV text and extract structured information with fallback"""
    
    print("=== SCRAPED CV TEXT ===")
    print(text[:1000] + "..." if len(text) > 1000 else text)
    print("=== END SCRAPED TEXT ===")
    
    # First try with Gemini AI
    gemini_result = enhance_parsing_with_gemini(text)
    if gemini_result:
        print("=== GEMINI PARSED DATA ===")
        print(json.dumps(gemini_result, indent=2))
        print("=== END GEMINI DATA ===")
        return gemini_result
    
    # Fallback to regex-based parsing if Gemini fails
    print("Gemini failed, using fallback parsing...")
    
    # Initialize the parsed data structure with only empty containers
    parsed_data = {
        'name': '',
        'email': '',
        'phone': '',
        'linkedin': '',
        'github': '',
        'website': '',
        'address': '',
        'education': [],
        'experience': [],
        'projects': [],
        'skills': {
            'languages': [],
            'frameworks': [],
            'tools': [],
            'libraries': [],
            'databases': [],
            'other': []
        },
        'certifications': [],
        'awards': [],
        'languages': []
    }
    
    lines = text.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    # Extract basic contact information
    for line in lines:
        # Email pattern
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)
        if email_match and not parsed_data['email']:
            parsed_data['email'] = email_match.group()
        
        # Phone pattern
        phone_match = re.search(r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})', line)
        if phone_match and not parsed_data['phone']:
            parsed_data['phone'] = phone_match.group()
        
        # LinkedIn pattern
        if 'linkedin.com' in line.lower() and not parsed_data['linkedin']:
            parsed_data['linkedin'] = line.strip()
        
        # GitHub pattern
        if 'github.com' in line.lower() and not parsed_data['github']:
            parsed_data['github'] = line.strip()
        
        # Website pattern (basic)
        if ('http' in line.lower() or 'www.' in line.lower()) and 'linkedin' not in line.lower() and 'github' not in line.lower() and not parsed_data['website']:
            parsed_data['website'] = line.strip()
    
    # Extract name (usually the first significant line)
    if lines and not parsed_data['name']:
        # Look for a line that might be a name (usually at the top, not an email/phone)
        for line in lines[:5]:
            if not re.search(r'[@()]', line) and len(line.split()) <= 4 and len(line) > 2:
                parsed_data['name'] = line
                break
    
    # Extract education, experience, projects, and skills
    current_section = None
    current_item = {}
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Identify sections
        if any(keyword in line_lower for keyword in ['education', 'academic']):
            current_section = 'education'
            continue
        elif any(keyword in line_lower for keyword in ['experience', 'work', 'employment', 'professional']):
            current_section = 'experience'
            continue
        elif any(keyword in line_lower for keyword in ['project', 'portfolio']):
            current_section = 'projects'
            continue
        elif any(keyword in line_lower for keyword in ['skill', 'technical', 'programming', 'languages']):
            current_section = 'skills'
            continue
        
        # Process content based on current section
        if current_section == 'education' and line:
            # Look for degree patterns
            if any(degree in line_lower for degree in ['bachelor', 'master', 'phd', 'associate', 'certificate']):
                if current_item:
                    parsed_data['education'].append(current_item)
                current_item = {'degree': line, 'institution': '', 'date': ''}
            elif current_item and not current_item['institution']:
                current_item['institution'] = line
            elif current_item and re.search(r'\d{4}', line):
                current_item['date'] = line
        
        elif current_section == 'experience' and line:
            # Look for job titles or company names
            if any(char in line for char in ['-', '|']) or re.search(r'\d{4}', line):
                if current_item:
                    parsed_data['experience'].append(current_item)
                current_item = {'title': line, 'company': '', 'date': '', 'description': []}
            elif current_item and not current_item.get('description'):
                current_item['description'] = [line]
            elif current_item:
                current_item['description'].append(line)
        
        elif current_section == 'projects' and line:
            if current_item and 'title' in current_item:
                parsed_data['projects'].append(current_item)
                current_item = {}
            current_item = {'title': line, 'description': '', 'technologies': ''}
        
        elif current_section == 'skills' and line:
            # Parse skills line by line
            if any(keyword in line_lower for keyword in ['language', 'programming']):
                skills_text = line.split(':')[-1] if ':' in line else line
                parsed_data['skills']['languages'] = [s.strip() for s in skills_text.split(',') if s.strip()]
            elif any(keyword in line_lower for keyword in ['framework']):
                skills_text = line.split(':')[-1] if ':' in line else line
                parsed_data['skills']['frameworks'] = [s.strip() for s in skills_text.split(',') if s.strip()]
            elif any(keyword in line_lower for keyword in ['tool', 'software']):
                skills_text = line.split(':')[-1] if ':' in line else line
                parsed_data['skills']['tools'] = [s.strip() for s in skills_text.split(',') if s.strip()]
    
    # Add the last item if it exists
    if current_item:
        if current_section == 'education':
            parsed_data['education'].append(current_item)
        elif current_section == 'experience':
            parsed_data['experience'].append(current_item)
        elif current_section == 'projects':
            parsed_data['projects'].append(current_item)
    
    # Clean up empty fields
    cleaned_data = {}
    for key, value in parsed_data.items():
        if key == 'skills':
            # Only include skill categories that have actual skills
            skills_cleaned = {k: v for k, v in value.items() if v}
            if skills_cleaned:
                cleaned_data[key] = skills_cleaned
        elif isinstance(value, list):
            # Only include lists that have items
            if value:
                cleaned_data[key] = value
        elif isinstance(value, str):
            # Only include strings that are not empty
            if value:
                cleaned_data[key] = value
        else:
            if value:
                cleaned_data[key] = value
    
    return cleaned_data

def clean_text_for_latex(text):
    """Clean text to be LaTeX-safe"""
    if not text:
        return ""
    
    # Handle case where text might be a list
    if isinstance(text, list):
        return [clean_text_for_latex(item) for item in text]
    
    # Convert to string if not already
    text = str(text)
    
    # First handle backslashes to avoid conflicts
    text = text.replace('\\', '\\textbackslash{}')
    
    # Replace problematic Unicode characters
    replacements = {
        '○': '\\textbullet',  # Unicode bullet
        '●': '\\textbullet',  # Black circle
        '•': '\\textbullet',  # Bullet
        '◦': '\\textbullet',  # White bullet
        '▪': '\\textbullet',  # Black small square
        '▫': '\\textbullet',  # White small square
        '–': '--',           # En dash
        '—': '---',          # Em dash
        ''': "'",            # Left single quotation mark
        ''': "'",            # Right single quotation mark
        '"': '"',            # Left double quotation mark
        '"': '"',            # Right double quotation mark
        '…': '...',          # Horizontal ellipsis
        '°': '\\textdegree', # Degree symbol
        '±': '\\textpm',     # Plus-minus
        '×': '\\texttimes',  # Multiplication sign
        '÷': '\\textdiv',    # Division sign
        '€': '\\texteuro',   # Euro sign
        '£': '\\textsterling', # Pound sign
        '¥': '\\textyen',    # Yen sign
        '©': '\\textcopyright', # Copyright
        '®': '\\textregistered', # Registered trademark
        '™': '\\texttrademark', # Trademark
    }
    
    # Apply replacements
    for unicode_char, latex_replacement in replacements.items():
        text = text.replace(unicode_char, latex_replacement)
    
    # Escape special LaTeX characters (excluding backslash which we handled first)
    latex_special_chars = {
        '&': '\\&',
        '%': '\\%',
        '$': '\\$',
        '#': '\\#',
        '^': '\\textasciicircum{}',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
    }
    
    for char, replacement in latex_special_chars.items():
        text = text.replace(char, replacement)
    
    return text

def generate_latex_resume(parsed_data):
    """Generate LaTeX resume using Jake's Resume template"""
    
    # Jake's Resume template with Unicode support
    latex_template = r"""
%-------------------------
% Resume in Latex
% Author : Jake Gutierrez
% Based off of: https://github.com/sb2nov/resume
% License : MIT
%------------------------

\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{textcomp}
\input{glyphtounicode}

%----------FONT OPTIONS----------
% sans-serif
% \usepackage[sfdefault]{FiraSans}
% \usepackage[sfdefault]{roboto}
% \usepackage[sfdefault]{noto-sans}
% \usepackage[default]{sourcesanspro}

% serif
% \usepackage{CormorantGaramond}
% \usepackage{charter}

\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Ensure that generate pdf is machine readable/ATS parsable
\pdfgentounicode=1

%-------------------------
% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%

\begin{document}

%----------HEADING----------
\begin{center}
    \textbf{\Huge \scshape """ + clean_text_for_latex(parsed_data.get('name', 'Name Not Found')) + r"""} \\ \vspace{1pt}"""

    # Build contact information dynamically
    contact_parts = []
    
    if parsed_data.get('phone'):
        contact_parts.append(clean_text_for_latex(parsed_data['phone']))
    
    if parsed_data.get('email'):
        email = clean_text_for_latex(parsed_data['email'])
        contact_parts.append(f"\\href{{mailto:{email}}}{{\\underline{{{email}}}}}")
    
    if parsed_data.get('linkedin'):
        linkedin_url = parsed_data['linkedin']
        if not linkedin_url.startswith('http'):
            linkedin_url = 'https://' + linkedin_url
        contact_parts.append(f"\\href{{{linkedin_url}}}{{\\underline{{LinkedIn}}}}")
    
    if parsed_data.get('github'):
        github_url = parsed_data['github']
        if not github_url.startswith('http'):
            github_url = 'https://' + github_url
        contact_parts.append(f"\\href{{{github_url}}}{{\\underline{{GitHub}}}}")
    
    if parsed_data.get('website'):
        website_url = parsed_data['website']
        if not website_url.startswith('http'):
            website_url = 'https://' + website_url
        contact_parts.append(f"\\href{{{website_url}}}{{\\underline{{Website}}}}")
    
    if contact_parts:
        latex_template += f"""
    \\small {' $|$ '.join(contact_parts)}"""
    
    latex_template += r"""
\end{center}"""

    # Add Education section only if education data exists
    if parsed_data.get('education'):
        latex_template += r"""

%-----------EDUCATION-----------
\section{Education}
  \resumeSubHeadingListStart"""
        
        for edu in parsed_data['education']:
            degree = clean_text_for_latex(edu.get('degree', ''))
            institution = clean_text_for_latex(edu.get('institution', ''))
            date = clean_text_for_latex(edu.get('date', ''))
            location = clean_text_for_latex(edu.get('location', ''))
            gpa = clean_text_for_latex(edu.get('gpa', ''))
            details = clean_text_for_latex(edu.get('details', ''))
            
            # Build the education entry
            latex_template += f"""
    \\resumeSubheading
      {{{degree}}}{{{date}}}
      {{{institution}}}{{{location}}}"""
            
            # Add GPA or details if they exist
            if gpa or details:
                latex_template += r"""
      \resumeItemListStart"""
                if gpa:
                    latex_template += f"""
        \\resumeItem{{GPA: {gpa}}}"""
                if details:
                    latex_template += f"""
        \\resumeItem{{{details}}}"""
                latex_template += r"""
      \resumeItemListEnd"""
        
        latex_template += r"""
  \resumeSubHeadingListEnd"""

    # Add Experience section only if experience data exists
    if parsed_data.get('experience'):
        latex_template += r"""

%-----------EXPERIENCE-----------
\section{Experience}
  \resumeSubHeadingListStart"""
        
        for exp in parsed_data['experience']:
            title = clean_text_for_latex(exp.get('title', ''))
            company = clean_text_for_latex(exp.get('company', ''))
            date = clean_text_for_latex(exp.get('date', ''))
            location = clean_text_for_latex(exp.get('location', ''))
            description = exp.get('description', [])
            
            latex_template += f"""
    \\resumeSubheading
      {{{title}}}{{{date}}}
      {{{company}}}{{{location}}}"""
            
            if description:
                latex_template += r"""
      \resumeItemListStart"""
                for desc in description[:4]:  # Limit to 4 bullet points
                    clean_desc = clean_text_for_latex(desc)
                    latex_template += f"""
        \\resumeItem{{{clean_desc}}}"""
                latex_template += r"""
      \resumeItemListEnd"""
        
        latex_template += r"""
  \resumeSubHeadingListEnd"""

    # Add Projects section only if projects data exists
    if parsed_data.get('projects'):
        latex_template += r"""

%-----------PROJECTS-----------
\section{Projects}
    \resumeSubHeadingListStart"""
        
        for project in parsed_data['projects']:
            title = clean_text_for_latex(project.get('title', ''))
            description = project.get('description', '')
            if isinstance(description, list):
                description = clean_text_for_latex(' '.join(description))
            else:
                description = clean_text_for_latex(description)
            technologies = clean_text_for_latex(project.get('technologies', ''))
            date = clean_text_for_latex(project.get('date', ''))
            link = project.get('link', '')
            
            # Build project title with technologies
            project_title = title
            if technologies:
                project_title += f" $|$ \\emph{{{technologies}}}"
            
            latex_template += f"""
      \\resumeProjectHeading
          {{\\textbf{{{project_title}}}}}{{{date}}}"""
            
            if description:
                latex_template += f"""
          \\resumeItemListStart
            \\resumeItem{{{description}}}"""
                if link:
                    latex_template += f"""
            \\resumeItem{{Link: \\href{{{link}}}{{\\underline{{{link}}}}}}}"""
                latex_template += r"""
          \resumeItemListEnd"""
        
        latex_template += r"""
    \resumeSubHeadingListEnd"""

    # Add Technical Skills section only if skills data exists
    if parsed_data.get('skills'):
        skills = parsed_data['skills']
        skill_lines = []
        
        if skills.get('languages'):
            clean_languages = [clean_text_for_latex(lang) for lang in skills['languages']]
            skill_lines.append(f"\\textbf{{Languages}}: {', '.join(clean_languages)}")
        
        if skills.get('frameworks'):
            clean_frameworks = [clean_text_for_latex(fw) for fw in skills['frameworks']]
            skill_lines.append(f"\\textbf{{Frameworks}}: {', '.join(clean_frameworks)}")
        
        if skills.get('tools'):
            clean_tools = [clean_text_for_latex(tool) for tool in skills['tools']]
            skill_lines.append(f"\\textbf{{Developer Tools}}: {', '.join(clean_tools)}")
        
        if skills.get('libraries'):
            clean_libraries = [clean_text_for_latex(lib) for lib in skills['libraries']]
            skill_lines.append(f"\\textbf{{Libraries}}: {', '.join(clean_libraries)}")
        
        if skills.get('databases'):
            clean_databases = [clean_text_for_latex(db) for db in skills['databases']]
            skill_lines.append(f"\\textbf{{Databases}}: {', '.join(clean_databases)}")
        
        if skills.get('other'):
            clean_other = [clean_text_for_latex(other) for other in skills['other']]
            skill_lines.append(f"\\textbf{{Other}}: {', '.join(clean_other)}")
        
        if skill_lines:
            latex_template += r"""

%-----------PROGRAMMING SKILLS-----------
\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     """ + ' \\\\\n     '.join(skill_lines) + r"""
    }}
 \end{itemize}"""

    # Add Certifications section only if certifications data exists
    if parsed_data.get('certifications'):
        latex_template += r"""

%-----------CERTIFICATIONS-----------
\section{Certifications}
  \resumeSubHeadingListStart"""
        
        for cert in parsed_data['certifications']:
            name = clean_text_for_latex(cert.get('name', ''))
            issuer = clean_text_for_latex(cert.get('issuer', ''))
            date = clean_text_for_latex(cert.get('date', ''))
            
            latex_template += f"""
    \\resumeSubheading
      {{{name}}}{{{date}}}
      {{{issuer}}}{{}}"""
        
        latex_template += r"""
  \resumeSubHeadingListEnd"""

    # Add Awards section only if awards data exists
    if parsed_data.get('awards'):
        latex_template += r"""

%-----------AWARDS-----------
\section{Awards \& Honors}
  \resumeItemListStart"""
        
        for award in parsed_data['awards']:
            clean_award = clean_text_for_latex(award)
            latex_template += f"""
    \\resumeItem{{{clean_award}}}"""
        
        latex_template += r"""
  \resumeItemListEnd"""

    # Add Languages section only if language data exists
    if parsed_data.get('languages'):
        latex_template += r"""

%-----------LANGUAGES-----------
\section{Languages}
  \resumeItemListStart"""
        
        for lang in parsed_data['languages']:
            clean_lang = clean_text_for_latex(lang)
            latex_template += f"""
    \\resumeItem{{{clean_lang}}}"""
        
        latex_template += r"""
  \resumeItemListEnd"""

    latex_template += r"""

%-------------------------------------------
\end{document}
"""

    return latex_template

def compile_latex_to_pdf(latex_content, output_filename):
    """Compile LaTeX content to PDF using pdflatex"""
    try:
        # Create a temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write LaTeX content to temporary file
            tex_file = os.path.join(temp_dir, 'resume.tex')
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            print(f"Attempting to compile LaTeX file: {tex_file}")
            
            # Try to compile with pdflatex
            try:
                # First pass
                result1 = subprocess.run([
                    'pdflatex', 
                    '-interaction=nonstopmode',
                    '-output-directory', temp_dir,
                    tex_file
                ], capture_output=True, text=True, cwd=temp_dir)
                
                if result1.returncode != 0:
                    print(f"First pdflatex pass failed with return code: {result1.returncode}")
                    print(f"STDOUT: {result1.stdout}")
                    print(f"STDERR: {result1.stderr}")
                    # Try to read the log file for more details
                    log_file = os.path.join(temp_dir, 'resume.log')
                    if os.path.exists(log_file):
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            print(f"LOG FILE CONTENT:\n{f.read()}")
                    return False
                
                # Second pass (for references)
                result2 = subprocess.run([
                    'pdflatex', 
                    '-interaction=nonstopmode',
                    '-output-directory', temp_dir,
                    tex_file
                ], capture_output=True, text=True, cwd=temp_dir)
                
                # Copy PDF to output directory
                pdf_source = os.path.join(temp_dir, 'resume.pdf')
                pdf_destination = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
                
                if os.path.exists(pdf_source):
                    with open(pdf_source, 'rb') as src, open(pdf_destination, 'wb') as dst:
                        dst.write(src.read())
                    print(f"PDF successfully generated: {pdf_destination}")
                    return True
                else:
                    print("PDF file was not generated")
                    return False
                    
            except subprocess.CalledProcessError as e:
                print(f"pdflatex compilation failed: {e}")
                return False
                
    except Exception as e:
        print(f"Error compiling LaTeX to PDF: {e}")
        return False

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Extract text based on file type
        if filename.lower().endswith('.pdf'):
            extracted_text = extract_text_from_pdf(file_path)
        elif filename.lower().endswith('.docx'):
            extracted_text = extract_text_from_docx(file_path)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        # Parse the extracted text using Gemini AI
        parsed_data = parse_cv_text(extracted_text)
        
        # Generate LaTeX
        latex_content = generate_latex_resume(parsed_data)
        
        # Save LaTeX file
        base_filename = filename.rsplit('.', 1)[0]
        latex_filename = f"{base_filename}_resume.tex"
        latex_path = os.path.join(app.config['OUTPUT_FOLDER'], latex_filename)
        
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        print(f"Generated LaTeX saved to: {latex_path}")
        print("=== GENERATED LATEX CONTENT (first 500 chars) ===")
        print(latex_content[:500] + "..." if len(latex_content) > 500 else latex_content)
        
        # Compile to PDF
        pdf_filename = f"{base_filename}_resume.pdf"
        pdf_compiled = compile_latex_to_pdf(latex_content, pdf_filename)
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'parsed_data': parsed_data,
            'latex_content': latex_content,
            'latex_download_url': f'/download/{latex_filename}',
            'pdf_compiled': pdf_compiled,
            'pdf_download_url': f'/download/{pdf_filename}' if pdf_compiled else None,
            'pdf_preview_url': f'/preview/{pdf_filename}' if pdf_compiled else None
        })
    
    return jsonify({'error': 'Invalid file type. Please upload PDF or DOCX files only.'}), 400

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/preview/<filename>')
def preview_pdf(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path) and filename.endswith('.pdf'):
        return send_file(file_path, mimetype='application/pdf')
    return jsonify({'error': 'PDF file not found'}), 404

@app.route('/result')
def result_page():
    return render_template('result.html')

@app.route('/preview', methods=['POST'])
def preview_latex():
    """Generate a preview of the LaTeX content"""
    data = request.get_json()
    latex_content = data.get('latex_content', '')
    
    if not latex_content:
        return jsonify({'error': 'No LaTeX content provided'}), 400
    
    # Save to temporary file and compile (optional feature)
    # This requires LaTeX installation on the server
    return jsonify({'success': True, 'message': 'LaTeX content ready for download'})

@app.route('/static/<filename>')
def static_files(filename):
    """Serve static files like images"""
    return send_file(os.path.join('static', filename))

if __name__ == '__main__':
    app.run(debug=True) 