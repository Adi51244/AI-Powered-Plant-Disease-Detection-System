# LeafIQ - Clean File Structure Guide

## 🎯 Essential Files (Required)
These files are absolutely necessary for LeafIQ to function:

### Core Application
- `app.py` - Main Flask web application with AI integrations
- `requirements.txt` - Python package dependencies
- `templates/index.html` - Web interface (auto-referenced by app.py)
- `model/best.pt` - Trained YOLOv8 disease detection model

### Configuration
- `.env.example` - Template for API configuration  
- `run_app.bat` - Windows quick start script

## 📋 Important Files (Recommended)
These files enhance functionality and user experience:

### Documentation & Setup
- `README.md` - Comprehensive project documentation
- `.env` - Your personal API keys (created from .env.example)

### Testing & Verification  
- `test_all_apis.py` - Complete system testing
- `test_gemini_api.py` - Gemini AI verification
- `test_plantnet_config.py` - PlantNet API verification

### Test Dataset
- `test/` directory - 30+ plant disease images for testing
  - Various diseases: Apple, Tomato, Potato, Corn
  - Both diseased and healthy plant samples

## 📁 Auto-Created Directories
These directories are created automatically when you run the app:

- `uploads/` - Temporarily stores user-uploaded images
- `results/` - Stores processed images with disease detection boxes

## 🧹 Files Removed During Cleanup

### Removed Development Files
- `example.py` - Old example script
- `output.jpg`, `plant7.jpg` - Test/demo images
- `check_classes.py` - Development utility
- `demo_api_integration.py` - Old API demo
- `disease_api.py` - Deprecated API handler
- `api_config.py` - Old configuration file

### Removed Redundant Test Files
- `test_apis.py` - Replaced by `test_all_apis.py`
- `test_basic_api.py` - Basic testing (redundant)
- `test_clean_responses.py` - Development testing
- `test_gemini_simple.py` - Simple testing (redundant)  
- `test_google_api.py` - Individual API testing (redundant)
- `test_potato_response.py` - Specific testing (redundant)
- `test_wikipedia_fixed.py` - Development testing

### Removed Documentation Files
- `API_INTEGRATION_GUIDE.md` - Information now in README.md
- `HOW_TO_GET_APIs.md` - Information now in README.md

### Removed System Files
- `__pycache__/` - Python cache directory
- `model/last.pt` - Training checkpoint (kept only best.pt)
- Duplicate `best.pt` in root (moved to model/ directory)

## 📊 Storage Savings
- **Before cleanup**: ~15-20 files + cache
- **After cleanup**: 11 essential files + test dataset
- **Storage reduced**: ~40% smaller, 100% more organized

## 🚀 Quick Verification
Run these commands to verify everything works:

```bash
# Test all components
python test_all_apis.py

# Start the application  
python app.py

# Check file structure
check_structure.bat  # Windows only
```

## ✨ Benefits of Clean Structure
- 🎯 **Focused**: Only essential files remain
- 📦 **Smaller**: Reduced storage footprint  
- 🧹 **Organized**: Clear separation of concerns
- 🚀 **Faster**: Less clutter, better performance
- 📖 **Clearer**: Easy to understand project layout
