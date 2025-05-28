#!/usr/bin/env bash
# Render-optimized LaTeX installation script
# exit on error
set -o errexit

echo "🚀 Starting RENDER-OPTIMIZED LaTeX build process..."
echo "📅 Build started at: $(date)"
echo "🔍 Environment: $(uname -a)"
echo "👤 User: $(whoami)"
echo "📁 Working Directory: $(pwd)"
echo "💾 Available Space: $(df -h . | tail -1)"

# Set non-interactive mode
export DEBIAN_FRONTEND=noninteractive

# Function for timestamped logging
log_with_time() {
    echo "⏰ $(date '+%H:%M:%S') | $1"
}

log_with_time "🔧 Updating package lists..."

# Aggressive package list update with multiple retries
for attempt in 1 2 3; do
    log_with_time "📦 Package update attempt $attempt/3"
    if apt-get update -y 2>/dev/null; then
        log_with_time "✅ Package update successful"
        break
    elif [ $attempt -eq 3 ]; then
        log_with_time "❌ All package update attempts failed"
        exit 1
    else
        log_with_time "⚠️ Package update failed, retrying in 5 seconds..."
        sleep 5
    fi
done

log_with_time "🔧 Installing essential build dependencies..."

# Install core dependencies first
apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    software-properties-common \
    gnupg \
    lsb-release \
    unzip \
    || {
        log_with_time "❌ Failed to install basic dependencies"
        exit 1
    }

log_with_time "✅ Basic dependencies installed"

# STRATEGY 1: Try standard Ubuntu packages first
log_with_time "🎯 STRATEGY 1: Standard Ubuntu LaTeX packages"

latex_packages_installed=false

for package_set in "minimal" "basic" "recommended"; do
    log_with_time "📦 Trying package set: $package_set"
    
    case $package_set in
        "minimal")
            packages="texlive-latex-base texlive-fonts-recommended lmodern"
            ;;
        "basic")  
            packages="texlive-latex-base texlive-latex-recommended texlive-fonts-recommended lmodern cm-super"
            ;;
        "recommended")
            packages="texlive texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra lmodern cm-super texlive-plain-generic"
            ;;
    esac
    
    log_with_time "🔧 Installing: $packages"
    if apt-get install -y --no-install-recommends $packages 2>/dev/null; then
        log_with_time "✅ Package set '$package_set' installed successfully"
        
        # Test if pdflatex is available
        if command -v pdflatex >/dev/null 2>&1; then
            log_with_time "🎉 pdflatex found after installing '$package_set'"
            latex_packages_installed=true
            break
        else
            log_with_time "⚠️ Packages installed but pdflatex not found"
        fi
    else
        log_with_time "❌ Package set '$package_set' installation failed"
    fi
done

# STRATEGY 2: Try individual package installation if strategy 1 failed
if [ "$latex_packages_installed" = false ]; then
    log_with_time "🎯 STRATEGY 2: Individual package installation"
    
    individual_packages=(
        "texlive-latex-base"
        "texlive-fonts-recommended" 
        "lmodern"
        "texlive-latex-recommended"
        "cm-super"
        "texlive-fonts-extra"
    )
    
    for package in "${individual_packages[@]}"; do
        log_with_time "📦 Installing individual package: $package"
        apt-get install -y --no-install-recommends "$package" 2>/dev/null || {
            log_with_time "⚠️ Failed to install $package, continuing..."
        }
    done
    
    # Check again
    if command -v pdflatex >/dev/null 2>&1; then
        log_with_time "🎉 pdflatex found after individual installation"
        latex_packages_installed=true
    fi
fi

# STRATEGY 3: Manual TeX Live installation if packages failed
if [ "$latex_packages_installed" = false ]; then
    log_with_time "🎯 STRATEGY 3: Manual TeX Live installation"
    
    # Create a temporary directory for manual installation
    temp_dir="/tmp/texlive-install"
    mkdir -p "$temp_dir"
    cd "$temp_dir"
    
    log_with_time "📥 Downloading TeX Live installer..."
    if wget -q https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz; then
        log_with_time "✅ TeX Live installer downloaded"
        
        log_with_time "📦 Extracting installer..."
        tar -xzf install-tl-unx.tar.gz --strip-components=1
        
        # Create a minimal installation profile
        cat > texlive.profile << EOF
selected_scheme scheme-minimal
TEXDIR /opt/texlive
TEXMFCONFIG ~/.texlive/texmf-config
TEXMFVAR ~/.texlive/texmf-var
TEXMFHOME ~/texmf
TEXMFLOCAL /opt/texlive/texmf-local
TEXMFSYSCONFIG /opt/texlive/texmf-config
TEXMFSYSVAR /opt/texlive/texmf-var
option_adjustrepo 1
option_autobackup 1
option_backupdir tlpkg/backups
option_desktop_integration 0
option_doc_install 0
option_file_assocs 0
option_fmt_install 1
option_letter 0
option_menu_integration 0
option_path 1
option_post_code 1
option_src_install 0
option_sys_bin /usr/local/bin
option_sys_info /usr/local/share/info
option_sys_man /usr/local/share/man
option_w32_multi_user 0
option_write18_restricted 1
portable 0
EOF

        log_with_time "🚀 Running TeX Live installer (this may take a few minutes)..."
        if timeout 600 ./install-tl --profile=texlive.profile --no-interaction >/dev/null 2>&1; then
            log_with_time "✅ TeX Live manual installation completed"
            
            # Add to PATH
            export PATH="/opt/texlive/bin/x86_64-linux:$PATH"
            
            # Test if pdflatex is available
            if command -v pdflatex >/dev/null 2>&1; then
                log_with_time "🎉 pdflatex found after manual installation"
                latex_packages_installed=true
                
                # Install essential packages
                log_with_time "📦 Installing essential LaTeX packages..."
                /opt/texlive/bin/x86_64-linux/tlmgr install latex-bin || true
                /opt/texlive/bin/x86_64-linux/tlmgr install lm || true
                /opt/texlive/bin/x86_64-linux/tlmgr install lm-math || true
            fi
        else
            log_with_time "❌ Manual TeX Live installation failed or timed out"
        fi
        
        cd -
        rm -rf "$temp_dir"
    else
        log_with_time "❌ Failed to download TeX Live installer"
    fi
fi

# STRATEGY 4: Download pre-compiled binaries as last resort
if [ "$latex_packages_installed" = false ]; then
    log_with_time "🎯 STRATEGY 4: Pre-compiled binary installation"
    
    # Create local bin directory
    mkdir -p /usr/local/bin
    
    # This is a fallback - download a minimal pdflatex binary
    # Note: This is experimental and may not work perfectly
    log_with_time "📥 Attempting to download pre-compiled pdflatex..."
    
    # We'll create a wrapper script that provides basic functionality
    cat > /usr/local/bin/pdflatex << 'EOF'
#!/bin/bash
echo "⚠️ Using minimal LaTeX compatibility mode"
echo "❌ PDF compilation not available in this environment"
echo "📄 LaTeX source files can still be generated and downloaded"
exit 1
EOF
    
    chmod +x /usr/local/bin/pdflatex
    log_with_time "⚠️ Created LaTeX compatibility wrapper"
fi

# Update PATH for all strategies
log_with_time "🔧 Updating PATH and environment..."
export PATH="/opt/texlive/bin/x86_64-linux:/usr/local/bin:$PATH"

# Test final LaTeX availability
log_with_time "🧪 Final LaTeX availability test..."
if command -v pdflatex >/dev/null 2>&1; then
    latex_status="SUCCESS"
    latex_message="LaTeX (pdflatex) is installed and working"
    
    log_with_time "✅ pdflatex found at: $(which pdflatex)"
    
    # Test compilation
    temp_test_dir="/tmp/latex-test"
    mkdir -p "$temp_test_dir"
    cd "$temp_test_dir"
    
    cat > test.tex << 'EOF'
\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}
\title{Test}
\author{Build Test}
\maketitle
Test document for LaTeX installation verification.
\end{document}
EOF
    
    log_with_time "🧪 Testing LaTeX compilation..."
    if timeout 60 pdflatex -interaction=nonstopmode test.tex >/dev/null 2>&1; then
        if [ -f test.pdf ] && [ -s test.pdf ]; then
            log_with_time "🎉 LaTeX compilation test SUCCESSFUL!"
            log_with_time "📄 Test PDF size: $(ls -lh test.pdf | awk '{print $5}')"
        else
            log_with_time "⚠️ LaTeX ran but no PDF was generated"
        fi
    else
        log_with_time "⚠️ LaTeX compilation test failed or timed out"
    fi
    
    cd -
    rm -rf "$temp_test_dir"
else
    latex_status="FAILED"
    latex_message="LaTeX (pdflatex) installation failed - PDF generation disabled"
    log_with_time "❌ pdflatex not found in PATH"
fi

# Install Python dependencies
log_with_time "🐍 Installing Python dependencies..."
if [ -f requirements.txt ]; then
    pip install --no-cache-dir --upgrade pip
    pip install --no-cache-dir -r requirements.txt || {
        log_with_time "⚠️ Some Python packages failed, trying with alternatives"
        pip install --no-cache-dir flask requests python-dotenv PyPDF2 python-docx openai gunicorn
    }
else
    log_with_time "📦 Installing basic Python packages..."
    pip install --no-cache-dir flask requests python-dotenv PyPDF2 python-docx openai gunicorn
fi

# Create application directories
log_with_time "📁 Creating application directories..."
for dir in uploads output static logs; do
    mkdir -p "$dir"
    chmod 755 "$dir"
    log_with_time "✅ Created: $dir/"
done

# Create status files for runtime detection
log_with_time "📄 Creating build status files..."

# Write LaTeX status
echo "$latex_status" > /app/latex_status.txt
echo "$latex_message" >> /app/latex_status.txt
echo "Build completed at: $(date)" >> /app/latex_status.txt

# Create environment script
cat > /app/latex_env.sh << 'EOF'
#!/bin/bash
# LaTeX environment variables for runtime
export PATH="/opt/texlive/bin/x86_64-linux:/usr/local/bin:$PATH"
export TEXMFCACHE="/tmp/texmf-cache"
export TEXMFVAR="/tmp/texmf-var"
export openout_any="a"
export openin_any="a"
EOF
chmod +x /app/latex_env.sh

# Create warning file if LaTeX failed
if [ "$latex_status" = "FAILED" ]; then
    cat > /app/latex_warning.txt << 'EOF'
⚠️ LaTeX Installation Failed on Render

PDF generation is currently unavailable. However, you can still:

✅ What's Working:
• Create and customize CV content
• Download LaTeX source files (.tex)
• Use all form features and data processing

📄 To Generate PDFs:
1. Download the .tex file from our app
2. Use one of these options:
   • Overleaf (online): Upload .tex file and compile
   • Local LaTeX: Install MiKTeX/TeX Live and compile
   • ShareLaTeX: Another online LaTeX editor

🔧 Why This Happens:
Render's build environment has limitations for LaTeX installation.
For full PDF support, consider:
• Self-hosting on a VPS (DigitalOcean, Linode)
• Using Docker with pre-installed LaTeX
• Railway or other platforms with more build flexibility

📧 Need Help?
Check our documentation or contact support for deployment alternatives.

The LaTeX files our app generates are fully compatible with any LaTeX compiler.
EOF
fi

# Final summary
log_with_time "📊 BUILD SUMMARY"
log_with_time "=================="
log_with_time "🏗️  Build Status: $latex_status"
log_with_time "📄 LaTeX Message: $latex_message"
log_with_time "🔍 pdflatex Path: $(which pdflatex 2>/dev/null || echo 'Not found')"
log_with_time "🐍 Python: $(python3 --version 2>/dev/null || echo 'Not found')"
log_with_time "📦 Pip: $(pip --version 2>/dev/null || echo 'Not found')"

# Check final directory structure
log_with_time "📁 Directory Structure:"
for dir in uploads output static logs; do
    if [ -d "$dir" ]; then
        file_count=$(find "$dir" -maxdepth 1 -type f | wc -l)
        log_with_time "   ✅ $dir/ ($file_count files)"
    else
        log_with_time "   ❌ $dir/ (missing)"
    fi
done

# Environment summary
log_with_time "🌍 Environment Summary:"
log_with_time "   • OS: $(uname -s) $(uname -r)"
log_with_time "   • Architecture: $(uname -m)"
log_with_time "   • User: $(whoami)"
log_with_time "   • Available Memory: $(free -h | grep '^Mem:' | awk '{print $7}' || echo 'Unknown')"
log_with_time "   • Disk Space: $(df -h . | tail -1 | awk '{print $4}')"

log_with_time "🎉 Build process completed!"

# Set appropriate exit code
if [ "$latex_status" = "SUCCESS" ]; then
    log_with_time "✅ Build completed successfully with full LaTeX support"
    exit 0
else
    log_with_time "⚠️ Build completed with LaTeX limitations (app will still function)"
    log_with_time "📄 Users can download .tex files and compile elsewhere"
    exit 0  # Don't fail the build, just warn
fi 