#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Starting build process..."

# Check if we're in Render environment
if [ -n "$RENDER" ]; then
    echo "🌐 Detected Render environment"
    
    # For Render, we need to use the system package manager more carefully
    echo "📦 Updating package list..."
    apt-get update -y
    
    # Install LaTeX packages with better error handling
    echo "📝 Installing LaTeX packages..."
    apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-fonts-recommended \
        texlive-latex-extra \
        texlive-fonts-extra \
        lmodern \
        || echo "⚠️  Some LaTeX packages failed to install"
    
    # Try minimal installation if full installation fails
    if ! command -v pdflatex &> /dev/null; then
        echo "⚠️  Full LaTeX installation failed, trying minimal installation..."
        apt-get install -y --no-install-recommends \
            texlive-latex-base \
            texlive-fonts-recommended \
            || echo "❌ Minimal LaTeX installation also failed"
    fi
else
    echo "💻 Local development environment detected"
    
    # For local development, try different package managers
    if command -v apt-get &> /dev/null; then
        echo "📦 Using apt-get for local installation..."
        sudo apt-get update
        sudo apt-get install -y \
            texlive-latex-base \
            texlive-fonts-recommended \
            texlive-fonts-extra \
            texlive-latex-extra \
            texlive-latex-recommended \
            texlive-plain-generic \
            texlive-bibtex-extra \
            lmodern \
            cm-super
    elif command -v brew &> /dev/null; then
        echo "🍺 Using Homebrew for macOS..."
        brew install --cask mactex
    elif command -v choco &> /dev/null; then
        echo "🍫 Using Chocolatey for Windows..."
        choco install miktex
    else
        echo "❌ No supported package manager found"
    fi
fi

# Verify LaTeX installation
echo "✅ Verifying LaTeX installation..."
if command -v pdflatex &> /dev/null; then
    echo "✅ pdflatex found at: $(which pdflatex)"
    pdflatex --version | head -3 || echo "⚠️  Could not get version info"
else
    echo "❌ pdflatex not found - PDF generation will not work"
    echo "🔧 The application will still work for LaTeX generation only"
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads output static

# Set up environment for LaTeX if available
if command -v pdflatex &> /dev/null; then
    echo "🎯 LaTeX environment ready"
    export LATEX_AVAILABLE=true
else
    echo "⚠️  LaTeX not available - running in LaTeX-only mode"
    export LATEX_AVAILABLE=false
fi

echo "🎉 Build completed!"
echo "📊 Build summary:"
echo "  - Python: $(python --version)"
echo "  - LaTeX: $(if command -v pdflatex &> /dev/null; then echo 'Available'; else echo 'Not available'; fi)"
echo "  - Output directory: $(ls -la output 2>/dev/null || echo 'Created')" 