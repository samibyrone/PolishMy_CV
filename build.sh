#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Starting build process..."

# Update package list
echo "📦 Updating package list..."
apt-get update

# Install LaTeX with all necessary packages
echo "📝 Installing LaTeX packages..."
apt-get install -y \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    texlive-latex-recommended \
    texlive-plain-generic \
    texlive-bibtex-extra \
    lmodern \
    cm-super

# Verify LaTeX installation
echo "✅ Verifying LaTeX installation..."
pdflatex --version || echo "⚠️  Warning: pdflatex not found"

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads output static

echo "🎉 Build completed successfully!" 