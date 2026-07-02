# Project Setup - Placement Guide

## Directory Structure

```
trading_ai_system_refactored/
├── trading_ai_system/
│   ├── __init__.py                    ← FROM: trading_ai_system__init__.py
│   ├── __version__.py                 ← FROM: __version__.py
│   ├── core/
│   │   ├── __init__.py                ← FROM: core__init__.py
│   │   └── core.py                    ← FROM: /mnt/user-data/uploads/core.py
│   ├── data/
│   │   ├── __init__.py                ← FROM: data__init__.py
│   │   └── data.py                    ← FROM: /mnt/user-data/uploads/data.py
│   ├── features/
│   │   ├── __init__.py                ← FROM: features__init__.py
│   │   └── features.py                ← FROM: /mnt/user-data/uploads/features.py
│   ├── models/
│   │   ├── __init__.py                ← FROM: models__init__.py
│   │   └── models.py                  ← FROM: /mnt/user-data/uploads/models.py
│   ├── strategy/
│   │   ├── __init__.py                ← FROM: strategy__init__.py
│   │   └── strategy.py                ← FROM: /mnt/user-data/uploads/strategy.py
│   ├── risk/
│   │   ├── __init__.py                ← FROM: risk__init__.py
│   │   └── risk.py                    ← FROM: /mnt/user-data/uploads/risk.py
│   ├── live/
│   │   ├── __init__.py                ← FROM: live__init__.py
│   │   └── live.py                    ← FROM: /mnt/user-data/uploads/live.py
│   └── utils/
│       ├── __init__.py                ← FROM: utils__init__.py
│       └── utils.py                   ← FROM: /mnt/user-data/uploads/utils.py
├── tests/
│   ├── __init__.py                    ← FROM: tests__init__.py
│   ├── test_core.py
│   ├── test_data.py
│   ├── test_features.py
│   ├── test_models.py
│   ├── test_strategy.py
│   ├── test_risk.py
│   ├── test_live.py
│   └── test_utils.py
├── configs/
│   ├── default.json
│   └── example.json
├── docs/
│   ├── index.md
│   ├── api.md
│   └── architecture.md
├── setup.py                           ← FROM: setup.py
├── pyproject.toml                     ← FROM: pyproject.toml
├── README.md                          ← FROM: README.md
├── LICENSE                            ← ADD: MIT License
├── .gitignore                         ← ADD: Standard Python .gitignore
├── CHANGELOG.md                       ← ADD: Version history
└── .pre-commit-config.yaml            ← ADD: Pre-commit hooks
```

## Step-by-Step Setup

### 1. Create Root Directory
```bash
mkdir -p trading_ai_system_refactored
cd trading_ai_system_refactored
```

### 2. Create Package Structure
```bash
# Main package
mkdir -p trading_ai_system/{core,data,features,models,strategy,risk,live,utils}

# Tests
mkdir -p tests

# Documentation & Config
mkdir -p configs docs
```

### 3. Copy Core Setup Files
```bash
# Copy these files to root directory:
cp setup.py trading_ai_system_refactored/
cp pyproject.toml trading_ai_system_refactored/
cp README.md trading_ai_system_refactored/
```

### 4. Copy __version__.py
```bash
cp __version__.py trading_ai_system_refactored/trading_ai_system/
```

### 5. Copy Main Package __init__.py
```bash
# Rename trading_ai_system__init__.py → __init__.py
cp trading_ai_system__init__.py trading_ai_system_refactored/trading_ai_system/__init__.py
```

### 6. Copy Module __init__.py Files
```bash
cp core__init__.py trading_ai_system_refactored/trading_ai_system/core/__init__.py
cp data__init__.py trading_ai_system_refactored/trading_ai_system/data/__init__.py
cp features__init__.py trading_ai_system_refactored/trading_ai_system/features/__init__.py
cp models__init__.py trading_ai_system_refactored/trading_ai_system/models/__init__.py
cp strategy__init__.py trading_ai_system_refactored/trading_ai_system/strategy/__init__.py
cp risk__init__.py trading_ai_system_refactored/trading_ai_system/risk/__init__.py
cp live__init__.py trading_ai_system_refactored/trading_ai_system/live/__init__.py
cp utils__init__.py trading_ai_system_refactored/trading_ai_system/utils/__init__.py
```

### 7. Copy Module Implementation Files
```bash
# Copy from /mnt/user-data/uploads/
cp /mnt/user-data/uploads/core.py trading_ai_system_refactored/trading_ai_system/core/
cp /mnt/user-data/uploads/data.py trading_ai_system_refactored/trading_ai_system/data/
cp /mnt/user-data/uploads/features.py trading_ai_system_refactored/trading_ai_system/features/
cp /mnt/user-data/uploads/models.py trading_ai_system_refactored/trading_ai_system/models/
cp /mnt/user-data/uploads/strategy.py trading_ai_system_refactored/trading_ai_system/strategy/
cp /mnt/user-data/uploads/risk.py trading_ai_system_refactored/trading_ai_system/risk/
cp /mnt/user-data/uploads/live.py trading_ai_system_refactored/trading_ai_system/live/
cp /mnt/user-data/uploads/utils.py trading_ai_system_refactored/trading_ai_system/utils/
```

### 8. Copy Tests __init__.py
```bash
cp tests__init__.py trading_ai_system_refactored/tests/__init__.py
```

### 9. Create Additional Configuration Files

#### .gitignore
```bash
cat > trading_ai_system_refactored/.gitignore << 'EOF'
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
```

#### LICENSE (MIT)
```bash
cat > trading_ai_system_refactored/LICENSE << 'EOF'
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
```

### 10. Install Package
```bash
cd trading_ai_system_refactored
pip install -e .
```

### 11. Verify Installation
```bash
python -c "import trading_ai_system; print(trading_ai_system.__version__)"
```

Expected output:
```
0.79.0
```

### 12. Run Syntax Check
```bash
python -m py_compile trading_ai_system/**/*.py
python -m py_compile tests/__init__.py
```

## File Mapping Summary

| File in Output | Destination in Project |
|---|---|
| `__version__.py` | `trading_ai_system/__version__.py` |
| `setup.py` | `./setup.py` |
| `pyproject.toml` | `./pyproject.toml` |
| `README.md` | `./README.md` |
| `trading_ai_system__init__.py` | `trading_ai_system/__init__.py` |
| `core__init__.py` | `trading_ai_system/core/__init__.py` |
| `data__init__.py` | `trading_ai_system/data/__init__.py` |
| `features__init__.py` | `trading_ai_system/features/__init__.py` |
| `models__init__.py` | `trading_ai_system/models/__init__.py` |
| `strategy__init__.py` | `trading_ai_system/strategy/__init__.py` |
| `risk__init__.py` | `trading_ai_system/risk/__init__.py` |
| `live__init__.py` | `trading_ai_system/live/__init__.py` |
| `utils__init__.py` | `trading_ai_system/utils/__init__.py` |
| `tests__init__.py` | `tests/__init__.py` |
| (from uploads) `core.py` | `trading_ai_system/core/core.py` |
| (from uploads) `data.py` | `trading_ai_system/data/data.py` |
| (from uploads) `features.py` | `trading_ai_system/features/features.py` |
| (from uploads) `models.py` | `trading_ai_system/models/models.py` |
| (from uploads) `strategy.py` | `trading_ai_system/strategy/strategy.py` |
| (from uploads) `risk.py` | `trading_ai_system/risk/risk.py` |
| (from uploads) `live.py` | `trading_ai_system/live/live.py` |
| (from uploads) `utils.py` | `trading_ai_system/utils/utils.py` |

## Notes

- **Naming Convention**: `module__init__.py` → `module/__init__.py` (rename when copying)
- **Import Updates**: The `__init__.py` files assume modules are named `core.py`, `data.py`, etc.
- **Dependencies**: Ensure `pyproject.toml` dependencies are installed before running
- **Version**: Update version in `__version__.py` when releasing new versions

## Verification Checklist

- [ ] Directory structure created
- [ ] All files copied to correct locations
- [ ] `__init__.py` files properly named and placed
- [ ] Module files renamed (remove `__init__` suffix)
- [ ] `.gitignore` created
- [ ] `LICENSE` created
- [ ] Package installed in development mode: `pip install -e .`
- [ ] Syntax validation passed: `python -m py_compile ...`
- [ ] Import test passed: `python -c "import trading_ai_system"`
- [ ] Version check passed: `python -c "import trading_ai_system; print(trading_ai_system.__version__)"`
