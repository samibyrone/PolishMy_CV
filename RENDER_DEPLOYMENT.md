# Render Deployment Guide for CVLatex

## 🚀 Deployment Steps

### 1. Prepare Your Repository
Ensure you have these files in your repository:
- `render.yaml` - Render service configuration
- `build.sh` - Build script with LaTeX installation
- `requirements.txt` - Python dependencies
- `app.py` - Main Flask application

### 2. Create Render Service
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Use the following settings:
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### 3. Environment Variables
Set these environment variables in Render:
- `GEMINI_API_KEY` - Your Google Gemini API key
- `OPENAI_API_KEY` - Your OpenAI API key (if using GPT)
- `FLASK_ENV` - Set to `production`

### 4. Deployment Process
- Push your changes to GitHub
- Render will automatically start building
- Build process includes LaTeX installation (may take 5-10 minutes)
- Service will be available at `https://your-service-name.onrender.com`

## 🔧 Troubleshooting

### PDF Generation Issues

If PDFs are not generating on Render, follow these steps:

#### Step 1: Check System Status
Visit: `https://your-app-url.onrender.com/debug/system`

This will show:
- Platform information
- LaTeX installation status
- Directory structure
- System configuration

#### Step 2: Test LaTeX Compilation
Visit: `https://your-app-url.onrender.com/debug/test-latex`

This will:
- Test LaTeX with a simple document
- Show detailed error messages
- Verify PDF generation pipeline

#### Step 3: Run Diagnostic Script
```bash
python test_render_deployment.py https://your-app-url.onrender.com
```

This comprehensive test will check:
- App connectivity
- System configuration
- LaTeX installation
- PDF compilation
- File download/preview

### Common Issues & Solutions

#### Issue 1: "pdflatex not found"
**Solution**: The build script failed to install LaTeX properly.
- Check Render build logs
- Ensure `build.sh` has execute permissions
- Verify the build command in `render.yaml`

#### Issue 2: "LaTeX compilation failed"
**Solutions**:
1. Missing LaTeX packages - update `build.sh` with additional packages
2. Memory/timeout issues - increase worker timeout in `render.yaml`
3. Permissions issues - ensure output directory is writable

#### Issue 3: "Files not found after generation"
**Solutions**:
1. Check directory permissions
2. Verify `OUTPUT_FOLDER` configuration
3. Ensure directories are created in build script

### LaTeX Packages
The build script installs these LaTeX packages:
- `texlive-latex-base` - Basic LaTeX
- `texlive-fonts-recommended` - Standard fonts
- `texlive-fonts-extra` - Additional fonts
- `texlive-latex-extra` - Extra LaTeX packages
- `texlive-latex-recommended` - Recommended packages
- `lmodern` - Latin Modern fonts
- `cm-super` - Computer Modern fonts

### Alternative Solutions

If PDF generation continues to fail on Render:

1. **LaTeX-only Mode**: Generate only LaTeX files and let users compile locally
2. **External Service**: Use a LaTeX compilation service API
3. **Client-side**: Use JavaScript LaTeX libraries (limited functionality)
4. **Different Platform**: Consider platforms with better LaTeX support

## 📋 Deployment Checklist

- [ ] Repository has all required files
- [ ] `build.sh` is executable
- [ ] Environment variables are set
- [ ] Render service is configured correctly
- [ ] Build completes successfully
- [ ] App responds to basic requests
- [ ] LaTeX is installed (`/debug/system`)
- [ ] PDF compilation works (`/debug/test-latex`)
- [ ] Create CV feature works end-to-end

## 🆘 Getting Help

If you continue to experience issues:

1. **Check Build Logs**: Review Render build logs for errors
2. **Test Locally**: Ensure everything works on your local machine
3. **Debug Endpoints**: Use `/debug/system` and `/debug/test-latex`
4. **Run Diagnostics**: Use `test_render_deployment.py`
5. **Contact Support**: Provide diagnostic output and build logs

## 💡 Performance Tips

- Use `--workers 2` to handle multiple requests
- Set `--timeout 120` for LaTeX compilation
- Consider caching compiled PDFs
- Monitor memory usage during builds
- Use environment variables for sensitive data

---

**Note**: LaTeX installation can take 5-10 minutes during the initial build. Subsequent builds are faster due to Render's caching. 