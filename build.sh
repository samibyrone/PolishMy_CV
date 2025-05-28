#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Starting build process for Render deployment..."
echo "📅 Build started at: $(date)"

# Function for detailed logging
log_step() {
    echo "📋 Step: $1"
    echo "⏰ Time: $(date)"
}

# Check environment
log_step "Environment Check"
echo "🔍 OS: $(uname -a)"
echo "🔍 User: $(whoami)"
echo "🔍 Working directory: $(pwd)"
echo "🔍 Available space: $(df -h . | tail -1)"

# Update package list with better error handling
log_step "Updating package list"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y || {
    echo "❌ Failed to update package list"
    apt-get update -y --fix-missing || true
}

# Install basic dependencies first
log_step "Installing basic dependencies"
apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common \
    || echo "⚠️ Some basic packages failed to install"

# Install LaTeX with comprehensive package list
log_step "Installing LaTeX packages"
echo "📝 Installing LaTeX distribution..."

# Method 1: Try full texlive installation
if apt-get install -y --no-install-recommends \
    texlive \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-plain-generic \
    texlive-science \
    lmodern \
    cm-super; then
    echo "✅ Full LaTeX installation successful"
else
    echo "⚠️ Full installation failed, trying minimal installation"
    
    # Method 2: Minimal installation
    apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-fonts-recommended \
        lmodern \
        || echo "❌ Even minimal LaTeX installation failed"
fi

# Verify LaTeX installation
log_step "Verifying LaTeX installation"
if command -v pdflatex >/dev/null 2>&1; then
    echo "✅ pdflatex found at: $(which pdflatex)"
    echo "📋 pdflatex version:"
    pdflatex --version | head -3 || true
    
    # Test basic compilation
    echo "🧪 Testing basic LaTeX compilation..."
    cat > /tmp/test.tex << 'EOF'
\documentclass{article}
\begin{document}
Test document for LaTeX verification.
\end{document}
EOF
    
    cd /tmp
    if timeout 30 pdflatex -interaction=nonstopmode test.tex >/dev/null 2>&1; then
        echo "✅ LaTeX compilation test successful"
        rm -f test.* || true
    else
        echo "❌ LaTeX compilation test failed"
    fi
    cd - >/dev/null
else
    echo "❌ pdflatex not found after installation"
    echo "🔍 Searching for LaTeX binaries:"
    find /usr -name "*latex*" -type f 2>/dev/null | head -10 || true
fi

# Install Python dependencies
log_step "Installing Python dependencies"
if [ -f requirements.txt ]; then
    echo "📦 Installing Python packages from requirements.txt"
    pip install --no-cache-dir -r requirements.txt || {
        echo "⚠️ Failed to install some Python packages, retrying with --force-reinstall"
        pip install --force-reinstall --no-cache-dir -r requirements.txt || true
    }
else
    echo "⚠️ requirements.txt not found"
fi

# Create necessary directories
log_step "Creating application directories"
mkdir -p uploads output static logs
chmod 755 uploads output static logs

# Set up logging
log_step "Setting up application logging"
touch logs/app.log logs/latex.log
chmod 644 logs/*.log

# Final verification
log_step "Final verification"
echo "📊 Build summary:"
echo "   - pdflatex available: $(command -v pdflatex >/dev/null 2>&1 && echo "✅ Yes" || echo "❌ No")"
echo "   - Python available: $(command -v python3 >/dev/null 2>&1 && echo "✅ Yes" || echo "❌ No")"
echo "   - pip available: $(command -v pip >/dev/null 2>&1 && echo "✅ Yes" || echo "❌ No")"
echo "   - uploads directory: $([ -d uploads ] && echo "✅ Yes" || echo "❌ No")"
echo "   - output directory: $([ -d output ] && echo "✅ Yes" || echo "❌ No")"

# Show disk usage
echo "💾 Disk usage after build:"
df -h . | tail -1

# Environment variables for runtime
log_step "Setting up runtime environment"
echo "export PATH=\$PATH:/usr/local/texlive/*/bin/*" >> ~/.bashrc
echo "export TEXMFCACHE=/tmp/texmf-cache" >> ~/.bashrc

echo "🎉 Build process completed at: $(date)"

# If LaTeX is still not available, create a warning file
if ! command -v pdflatex >/dev/null 2>&1; then
    echo "⚠️ Creating LaTeX warning file"
    cat > latex_warning.txt << 'EOF'
WARNING: LaTeX (pdflatex) is not available on this system.
PDF generation will be disabled.
Users can still download LaTeX source files and compile them locally.

Alternative solutions:
1. Use Overleaf (online LaTeX editor)
2. Install MiKTeX or TeX Live locally
3. Use self-hosted deployment with VPS
EOF
fi

echo "✅ Build script execution completed" 