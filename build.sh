#!/usr/bin/env bash
# exit on error
set -o errexit

# Install LaTeX
apt-get update
apt-get install -y texlive-latex-base texlive-fonts-recommended texlive-fonts-extra texlive-latex-extra

# Install Python dependencies
pip install -r requirements.txt 