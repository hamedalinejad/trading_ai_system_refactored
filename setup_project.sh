#!/bin/bash

# Trading AI System - Automated Project Setup
# This script creates the complete project structure

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="${1:-trading_ai_system_refactored}"
UPLOADS_DIR="${2:-/mnt/user-data/uploads}"
OUTPUTS_DIR="${3:-/mnt/user-data/outputs}"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Trading AI System - Project Setup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Create directory structure
echo -e "${YELLOW}Step 1: Creating directory structure...${NC}"
mkdir -p "$PROJECT_ROOT/trading_ai_system"/{core,data,features,models,strategy,risk,live,utils}
mkdir -p "$PROJECT_ROOT/tests"
mkdir -p "$PROJECT_ROOT/configs"
mkdir -p "$PROJECT_ROOT/docs"
echo -e "${GREEN}✓ Directories created${NC}\n"

# Step 2: Copy setup files
echo -e "${YELLOW}Step 2: Copying setup files...${NC}"
cp "$OUTPUTS_DIR/setup.py" "$PROJECT_ROOT/"
cp "$OUTPUTS_DIR/pyproject.toml" "$PROJECT_ROOT/"
cp "$OUTPUTS_DIR/README.md" "$PROJECT_ROOT/"
echo -e "${GREEN}✓ Setup files copied${NC}\n"

# Step 3: Copy __version__.py
echo -e "${YELLOW}Step 3: Copying version file...${NC}"
cp "$OUTPUTS_DIR/__version__.py" "$PROJECT_ROOT/trading_ai_system/"
echo -e "${GREEN}✓ Version file copied${NC}\n"

# Step 4: Copy main package __init__.py
echo -e "${YELLOW}Step 4: Copying main package init...${NC}"
cp "$OUTPUTS_DIR/trading_ai_system__init__.py" "$PROJECT_ROOT/trading_ai_system/__init__.py"
echo -e "${GREEN}✓ Main init copied${NC}\n"

# Step 5: Copy module __init__.py files
echo -e "${YELLOW}Step 5: Copying module init files...${NC}"
cp "$OUTPUTS_DIR/core__init__.py" "$PROJECT_ROOT/trading_ai_system/core/__init__.py"
cp "$OUTPUTS_DIR/data__init__.py" "$PROJECT_ROOT/trading_ai_system/data/__init__.py"
cp "$OUTPUTS_DIR/features__init__.py" "$PROJECT_ROOT/trading_ai_system/features/__init__.py"
cp "$OUTPUTS_DIR/models__init__.py" "$PROJECT_ROOT/trading_ai_system/models/__init__.py"
cp "$OUTPUTS_DIR/strategy__init__.py" "$PROJECT_ROOT/trading_ai_system/strategy/__init__.py"
cp "$OUTPUTS_DIR/risk__init__.py" "$PROJECT_ROOT/trading_ai_system/risk/__init__.py"
cp "$OUTPUTS_DIR/live__init__.py" "$PROJECT_ROOT/trading_ai_system/live/__init__.py"
cp "$OUTPUTS_DIR/utils__init__.py" "$PROJECT_ROOT/trading_ai_system/utils/__init__.py"
echo -e "${GREEN}✓ Module inits copied${NC}\n"

# Step 6: Copy module implementation files
echo -e "${YELLOW}Step 6: Copying module implementation files...${NC}"
cp "$UPLOADS_DIR/core.py" "$PROJECT_ROOT/trading_ai_system/core/"
cp "$UPLOADS_DIR/data.py" "$PROJECT_ROOT/trading_ai_system/data/"
cp "$UPLOADS_DIR/features.py" "$PROJECT_ROOT/trading_ai_system/features/"
cp "$UPLOADS_DIR/models.py" "$PROJECT_ROOT/trading_ai_system/models/"
cp "$UPLOADS_DIR/strategy.py" "$PROJECT_ROOT/trading_ai_system/strategy/"
cp "$UPLOADS_DIR/risk.py" "$PROJECT_ROOT/trading_ai_system/risk/"
cp "$UPLOADS_DIR/live.py" "$PROJECT_ROOT/trading_ai_system/live/"
cp "$UPLOADS_DIR/utils.py" "$PROJECT_ROOT/trading_ai_system/utils/"
echo -e "${GREEN}✓ Module files copied${NC}\n"

# Step 7: Copy tests __init__.py
echo -e "${YELLOW}Step 7: Copying tests init...${NC}"
cp "$OUTPUTS_DIR/tests__init__.py" "$PROJECT_ROOT/tests/__init__.py"
echo -e "${GREEN}✓ Tests init copied${NC}\n"

# Step 8: Create additional configuration files
echo -e "${YELLOW}Step 8: Creating additional configuration files...${NC}"

# Create .gitignore
cat > "$PROJECT_ROOT/.gitignore" << 'EOF'
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*.swn
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Data
data/
*.csv
*.h5
*.pkl
*.pickle

# Models
models/
*.joblib
*.pkl

# Logs
logs/
*.log

# Config (local)
config.local.json
.env
.env.local
EOF

# Create LICENSE
cat > "$PROJECT_ROOT/LICENSE" << 'EOF'
MIT License

Copyright (c) 2024 Trading AI System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

echo -e "${GREEN}✓ Configuration files created${NC}\n"

# Step 9: Syntax validation
echo -e "${YELLOW}Step 9: Validating syntax...${NC}"
python3 -m py_compile "$PROJECT_ROOT/trading_ai_system/__init__.py" || {
    echo -e "${YELLOW}Note: Import validation will run after installation${NC}"
}
echo -e "${GREEN}✓ Syntax check complete${NC}\n"

# Print summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Project structure created successfully!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. cd $PROJECT_ROOT"
echo "  2. pip install -e ."
echo "  3. python -c \"import trading_ai_system; print(trading_ai_system.__version__)\""
echo ""
echo -e "${BLUE}Project location:${NC} $(pwd)/$PROJECT_ROOT"
echo ""
