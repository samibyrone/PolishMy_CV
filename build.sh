#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Starting Render build process for CVLatex..."
echo "📅 Build started at: $(date)"
echo "🔍 Environment: $(uname -a)"
echo "👤 User: $(whoami)"
echo "📁 PWD: $(pwd)"

# Function for detailed logging
log_step() {
    echo ""
    echo "=================================================="
    echo "📋 $1"
    echo "⏰ $(date)"
    echo "=================================================="
}

# Function to check command availability
check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "✅ $1 is available at: $(which $1)"
        return 0
    else
        echo "❌ $1 is not available"
        return 1
    fi
}

# Function to install LaTeX packages
install_latex_packages() {
    local method="$1"
    echo "🔧 Attempting LaTeX installation method: $method"
    
    case $method in
        "minimal")
            apt-get install -y --no-install-recommends \
                texlive-latex-base \
                texlive-fonts-recommended \
                lmodern \
                || return 1
            ;;
        "basic")
            apt-get install -y --no-install-recommends \
                texlive-latex-base \
                texlive-latex-recommended \
                texlive-fonts-recommended \
                texlive-fonts-extra \
                lmodern \
                cm-super \
                || return 1
            ;;
        "full")
            apt-get install -y --no-install-recommends \
                texlive \
                texlive-latex-base \
                texlive-latex-recommended \
                texlive-latex-extra \
                texlive-fonts-recommended \
                texlive-fonts-extra \
                texlive-plain-generic \
                lmodern \
                cm-super \
                || return 1
            ;;
        "alternative")
            # Try individual package installation
            for package in texlive-latex-base texlive-fonts-recommended lmodern; do
                echo "🔧 Installing $package..."
                apt-get install -y --no-install-recommends "$package" || {
                    echo "⚠️ Failed to install $package, continuing..."
                }
            done
            ;;
        *)
            echo "❌ Unknown installation method: $method"
            return 1
            ;;
    esac
}

# Update system
log_step "Updating package lists"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y || {
    echo "⚠️ Primary update failed, trying with --fix-missing"
    apt-get update -y --fix-missing || {
        echo "❌ Package update failed completely"
        exit 1
    }
}

# Install basic dependencies
log_step "Installing basic dependencies"
apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    gnupg \
    software-properties-common \
    python3 \
    python3-pip \
    || {
        echo "❌ Failed to install basic dependencies"
        exit 1
    }

# Try multiple LaTeX installation strategies
log_step "Installing LaTeX - Multiple Strategy Approach"

latex_installed=false
for method in "minimal" "basic" "alternative"; do
    echo ""
    echo "🎯 Trying LaTeX installation method: $method"
    
    if install_latex_packages "$method"; then
        echo "✅ LaTeX installation method '$method' succeeded"
        
        # Test if pdflatex is available
        if check_command "pdflatex"; then
            latex_installed=true
            break
        else
            echo "⚠️ Packages installed but pdflatex not found, trying next method..."
        fi
    else
        echo "❌ LaTeX installation method '$method' failed, trying next..."
    fi
done

# Final LaTeX verification
log_step "LaTeX Installation Verification"
if check_command "pdflatex"; then
    latex_installed=true
    echo "✅ pdflatex found and available!"
    
    # Get version info
    echo "📋 pdflatex version:"
    pdflatex --version | head -3 || echo "⚠️ Could not get version info"
    
    # Test basic compilation
    echo "🧪 Testing basic LaTeX compilation..."
    cat > /tmp/test_latex.tex << 'EOF'
\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}
\title{Test Document}
\author{Render Build Test}
\maketitle
This is a test document to verify LaTeX installation.
\end{document}
EOF
    
    cd /tmp
    if timeout 30 pdflatex -interaction=nonstopmode test_latex.tex >/dev/null 2>&1; then
        if [ -f test_latex.pdf ] && [ -s test_latex.pdf ]; then
            echo "✅ LaTeX compilation test SUCCESSFUL"
            echo "📄 Test PDF created: $(ls -lh test_latex.pdf)"
        else
            echo "❌ LaTeX compilation failed - no PDF created"
        fi
    else
        echo "❌ LaTeX compilation test failed or timed out"
    fi
    
    # Cleanup test files
    rm -f test_latex.* 2>/dev/null || true
    cd - >/dev/null
    
else
    echo "❌ pdflatex not found after all installation attempts"
    latex_installed=false
    
    # Try to find any latex-related binaries
    echo "🔍 Searching for any LaTeX binaries..."
    find /usr /opt -name "*latex*" -type f 2>/dev/null | head -10 || echo "No LaTeX binaries found"
fi

# Install Python dependencies
log_step "Installing Python dependencies"
if [ -f requirements.txt ]; then
    echo "📦 Installing from requirements.txt..."
    pip install --no-cache-dir --upgrade pip
    pip install --no-cache-dir -r requirements.txt || {
        echo "⚠️ Some packages failed, trying with --force-reinstall"
        pip install --force-reinstall --no-cache-dir -r requirements.txt
    }
else
    echo "⚠️ requirements.txt not found - installing basic packages"
    pip install --no-cache-dir flask requests python-dotenv PyPDF2 python-docx openai gunicorn
fi

# Create application directories
log_step "Setting up application directories"
for dir in uploads output static logs; do
    mkdir -p "$dir"
    chmod 755 "$dir"
    echo "✅ Created directory: $dir"
done

# Set up logging
touch logs/app.log logs/latex.log 2>/dev/null || true
chmod 644 logs/*.log 2>/dev/null || true

# Configure LaTeX environment
log_step "Configuring LaTeX environment"
if [ "$latex_installed" = true ]; then
    # Set up environment variables for LaTeX
    echo "🔧 Setting up LaTeX environment variables..."
    
    # Create environment setup script
    cat > /app/latex_env.sh << 'EOF'
#!/bin/bash
# LaTeX environment setup
export PATH="/usr/bin:/usr/local/bin:$PATH"
export TEXMFCACHE="/tmp/texmf-cache"
export TEXMFVAR="/tmp/texmf-var"
export openout_any="a"
export openin_any="a"
EOF
    
    chmod +x /app/latex_env.sh
    
    # Source it in the current session
    source /app/latex_env.sh
    
    echo "✅ LaTeX environment configured"
else
    echo "⚠️ Skipping LaTeX environment setup - LaTeX not available"
fi

# Create status indicators
log_step "Creating deployment status files"
if [ "$latex_installed" = true ]; then
    echo "SUCCESS" > /app/latex_status.txt
    echo "LaTeX (pdflatex) is installed and working" >> /app/latex_status.txt
    echo "Build completed at: $(date)" >> /app/latex_status.txt
else
    echo "FAILED" > /app/latex_status.txt
    echo "LaTeX (pdflatex) installation failed" >> /app/latex_status.txt
    echo "PDF generation will be disabled" >> /app/latex_status.txt
    echo "Build completed at: $(date)" >> /app/latex_status.txt
    
    # Create warning for users
    cat > /app/latex_warning.txt << 'EOF'
⚠️ WARNING: LaTeX (pdflatex) is not available on this deployment.

PDF generation is currently disabled. You can still:
1. Download LaTeX source files (.tex)
2. Compile them locally using:
   - MiKTeX (Windows)
   - TeX Live (Linux/Mac)
   - Overleaf (online)

For a deployment with PDF generation, consider:
- Using a VPS with manual LaTeX installation
- Self-hosting with Docker
- Using Vercel/Railway with custom LaTeX setup

Contact support if you need help with alternative deployment options.
EOF
fi

# Final summary
log_step "Build Summary"
echo "📊 Final Build Status:"
echo "   - Build started: $(head -2 /app/latex_status.txt | tail -1)"
echo "   - LaTeX status: $(head -1 /app/latex_status.txt)"
echo "   - pdflatex available: $(command -v pdflatex >/dev/null 2>&1 && echo "✅ YES" || echo "❌ NO")"
echo "   - Python available: $(command -v python3 >/dev/null 2>&1 && echo "✅ YES" || echo "❌ NO")"
echo "   - pip available: $(command -v pip >/dev/null 2>&1 && echo "✅ YES" || echo "❌ NO")"

# Check directory structure
echo "📁 Directory structure:"
for dir in uploads output static logs; do
    if [ -d "$dir" ]; then
        echo "   ✅ $dir/ ($(ls -la "$dir" | wc -l) items)"
    else
        echo "   ❌ $dir/ (missing)"
    fi
done

# Show disk usage
echo "💾 Disk usage:"
df -h . | tail -1

# Environment info for debugging
echo "🔍 Environment summary:"
echo "   - OS: $(uname -s)"
echo "   - Architecture: $(uname -m)"
echo "   - User: $(whoami)"
echo "   - Working dir: $(pwd)"
echo "   - PATH: ${PATH:0:200}..."

echo ""
echo "🎉 Build process completed at: $(date)"
echo "✅ Application is ready to deploy"

# If LaTeX failed, exit with warning but don't fail the build
if [ "$latex_installed" = false ]; then
    echo ""
    echo "⚠️  NOTE: LaTeX is not available - application will run in LaTeX-only mode"
    echo "📄 Users can still download .tex files and compile them externally"
fi

exit 0 