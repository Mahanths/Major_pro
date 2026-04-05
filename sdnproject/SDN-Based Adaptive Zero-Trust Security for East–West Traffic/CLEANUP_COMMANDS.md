# Quick Cleanup Commands

Run these commands in your project directory to clean up and organize:

## 🧹 CLEANUP SCRIPT (SAFE TO RUN)

```bash
#!/bin/bash
# Safe cleanup script - removes only unnecessary files

echo "🧹 Starting project cleanup..."

# 1. Remove virtual environment (saves 811 MB!)
if [ -d "venv" ]; then
    echo "  Removing venv/ directory... (saves 811 MB)"
    rm -rf venv/
fi

# 2. Remove empty directories
if [ -d "controller" ] && [ ! "$(ls -A controller)" ]; then
    echo "  Removing empty controller/ directory..."
    rm -rf controller/
fi

# 3. Remove log files
if [ -f "brain.log" ]; then
    echo "  Removing brain.log..."
    rm -f brain.log
fi

# 4. Remove Python cache
echo "  Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# 5. Remove .pytest cache
if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache
fi

echo "✅ Cleanup complete!"
echo ""
echo "📊 Current size:"
du -sh . 2>/dev/null | awk '{print "   Total: " $1}'
```

## 🚀 One-Line Cleanup

Copy and paste this single command:

```bash
rm -rf venv/ controller/ *.log 2>/dev/null; find . -name __pycache__ -exec rm -rf {} + 2>/dev/null; find . -name "*.pyc" -delete 2>/dev/null; echo "✅ Cleanup done!"
```

## 📊 Check Before & After

```bash
# Before cleanup
echo "Before cleanup:"
du -sh . && find . -name "*.pkl" -o -name "*.py" -o -name "*.csv" | wc -l

# Run cleanup commands...

# After cleanup  
echo "After cleanup:"
du -sh . && find . -name "*.pkl" -o -name "*.py" -o -name "*.csv" | wc -l
```

## 📁 Organize into Subdirectories

```bash
# Create organized structure
mkdir -p src models docs planning training_scripts

# Move files to organized locations
mv ids_pipeline.py test_runner.py test_system.py src/
mv ids_*.pkl models/
mv IDS_PIPELINE_*.md docs/
mv PIPELINE_*.md docs/
mv SESSION_SUMMARY.md docs/
mv plan_files/* planning/ 2>/dev/null
rmdir plan_files 2>/dev/null

echo "✅ Files organized!"
```

## 🔄 Git Configuration

```bash
# Create .gitignore
cat > .gitignore << 'EOF'
# Virtual Environment
venv/
env/
.venv/

# Python Cache
__pycache__/
*.pyc
*.pyo
*.egg-info/
.pytest_cache/

# IDE
.vscode/
.idea/
.DS_Store

# Logs
*.log
brain.log

# OS
Thumbs.db
*~
EOF

# Commit changes
git add .gitignore
git commit -m "Add .gitignore to exclude venv and cache"
git push origin master

echo "✅ Git configured!"
```

## 📋 Full Cleanup & Reorganize (All Steps)

Run these commands in sequence:

```bash
# Step 1: Backup (just in case)
echo "Creating backup..."
cp -r . ../project_backup_$(date +%Y%m%d)

# Step 2: Clean cache and logs
echo "Cleaning cache and logs..."
rm -rf venv/ controller/ *.log 2>/dev/null
find . -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name .pytest_cache -exec rm -rf {} + 2>/dev/null

# Step 3: Create organized structure
echo "Organizing files..."
mkdir -p src models docs planning

# Step 4: Move files
mv ids_pipeline.py test_runner.py test_system.py src/ 2>/dev/null
mv ids_*.pkl models/ 2>/dev/null
mv IDS_PIPELINE_*.md PIPELINE_*.md SESSION_SUMMARY.md docs/ 2>/dev/null
mv EXECUTIVE_SUMMARY.txt QUICK_REFERENCE_CARD.md docs/ 2>/dev/null
mv BASIC_COMMANDS_REFERENCE.md docs/ 2>/dev/null

# Step 5: Configure Git
cat > .gitignore << 'EOF'
venv/
env/
.venv/
__pycache__/
*.pyc
*.log
.vscode/
.DS_Store
EOF

git add .
git commit -m "Cleanup: Remove venv, organize files, add .gitignore"
git push origin master

# Step 6: Show results
echo ""
echo "✅ Cleanup and organization complete!"
echo ""
echo "📊 Space saved:"
echo "   Size: $(du -sh . 2>/dev/null | awk '{print $1}')"
echo ""
echo "📁 New structure:"
ls -la | grep "^d"
```

## ✅ Verify Everything Still Works

After cleanup, verify your setup:

```bash
# Recreate venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r brain/requirements.txt

# Check models are there
ls -la models/

# Test pipeline (optional)
python3 src/ids_pipeline.py --help

echo "✅ All verified!"
```

## 📊 Results You'll See

**Before:**
```
Total size: 1.2 GB
  venv/          811 MB  (removed)
  data/          216 MB  (kept)
  training/       71 MB  (kept)
  brain/           4 MB  (kept)
  ids_model.pkl   70 MB  (kept)
  other files     14 MB  (kept)
```

**After:**
```
Total size: 362 MB (-70%)
  data/          216 MB
  training/       71 MB
  brain/           4 MB
  ids_model.pkl   70 MB
  other files      1 MB
```

## 🎯 Key Points

✅ **KEEP:**
- `ids_*.pkl` - Your trained model (most important!)
- `data/*.csv` - Training data
- All `.py` files
- All `.md` documentation

❌ **REMOVE:**
- `venv/` - Can recreate anytime
- `__pycache__/` - Auto-generated
- `*.log` - Can regenerate
- Empty directories

## 🔗 Related Files

See `PROJECT_STRUCTURE_GUIDE.md` for detailed information about:
- Full directory structure
- What each file does
- Why to keep/remove files
- Best practices
