@echo off
REM Trading AI System - Automated Project Setup (Windows)

setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM Configuration
set "PROJECT_ROOT=trading_ai_system_refactored"
set "OUTPUTS_DIR=."

echo.
echo ===============================================================
echo Trading AI System - Project Setup (Windows)
echo ===============================================================
echo.

REM Step 1: Create directory structure
echo Step 1: Creating directory structure...
mkdir "%PROJECT_ROOT%\trading_ai_system\core" 2>nul
mkdir "%PROJECT_ROOT%\trading_ai_system\data" 2>nul
mkdir "%PROJECT_ROOT%\trading_ai_system\features" 2>nul
mkdir "%PROJECT_ROOT%\trading_ai_system\models" 2>nul
mkdir "%PROJECT_ROOT%\trading_ai_system\strategy" 2>nul
mkdir "%PROJECT_ROOT%\trading_ai_system\risk" 2>nul
mkdir "%PROJECT_ROOT%\trading_ai_system\live" 2>nul
mkdir "%PROJECT_ROOT%\trading_ai_system\utils" 2>nul
mkdir "%PROJECT_ROOT%\tests" 2>nul
mkdir "%PROJECT_ROOT%\configs" 2>nul
mkdir "%PROJECT_ROOT%\docs" 2>nul
echo ✓ Directories created
echo.

REM Step 2: Copy setup files
echo Step 2: Copying setup files...
copy /Y "%OUTPUTS_DIR%\setup.py" "%PROJECT_ROOT%\" >nul
copy /Y "%OUTPUTS_DIR%\pyproject.toml" "%PROJECT_ROOT%\" >nul
copy /Y "%OUTPUTS_DIR%\README.md" "%PROJECT_ROOT%\" >nul
echo ✓ Setup files copied
echo.

REM Step 3: Copy version file
echo Step 3: Copying version file...
copy /Y "%OUTPUTS_DIR%\__version__.py" "%PROJECT_ROOT%\trading_ai_system\" >nul
echo ✓ Version file copied
echo.

REM Step 4: Copy main package init
echo Step 4: Copying main package init...
copy /Y "%OUTPUTS_DIR%\trading_ai_system__init__.py" "%PROJECT_ROOT%\trading_ai_system\__init__.py" >nul
echo ✓ Main init copied
echo.

REM Step 5: Copy module init files
echo Step 5: Copying module init files...
copy /Y "%OUTPUTS_DIR%\core__init__.py" "%PROJECT_ROOT%\trading_ai_system\core\__init__.py" >nul
copy /Y "%OUTPUTS_DIR%\data__init__.py" "%PROJECT_ROOT%\trading_ai_system\data\__init__.py" >nul
copy /Y "%OUTPUTS_DIR%\features__init__.py" "%PROJECT_ROOT%\trading_ai_system\features\__init__.py" >nul
copy /Y "%OUTPUTS_DIR%\models__init__.py" "%PROJECT_ROOT%\trading_ai_system\models\__init__.py" >nul
copy /Y "%OUTPUTS_DIR%\strategy__init__.py" "%PROJECT_ROOT%\trading_ai_system\strategy\__init__.py" >nul
copy /Y "%OUTPUTS_DIR%\risk__init__.py" "%PROJECT_ROOT%\trading_ai_system\risk\__init__.py" >nul
copy /Y "%OUTPUTS_DIR%\live__init__.py" "%PROJECT_ROOT%\trading_ai_system\live\__init__.py" >nul
copy /Y "%OUTPUTS_DIR%\utils__init__.py" "%PROJECT_ROOT%\trading_ai_system\utils\__init__.py" >nul
echo ✓ Module inits copied
echo.

REM Step 6: Copy module files (NOTE: Adjust path to uploads directory)
echo Step 6: Copying module implementation files...
echo Note: Update the paths below to match your actual uploads directory
echo Example: copy /Y "C:\path\to\uploads\core.py" ...
echo.
REM copy /Y "..\uploads\core.py" "%PROJECT_ROOT%\trading_ai_system\core\" >nul
REM copy /Y "..\uploads\data.py" "%PROJECT_ROOT%\trading_ai_system\data\" >nul
REM etc...
echo ⚠ Please manually copy the uploaded .py files to their destinations
echo   or update the paths in this script
echo.

REM Step 7: Copy tests init
echo Step 7: Copying tests init...
copy /Y "%OUTPUTS_DIR%\tests__init__.py" "%PROJECT_ROOT%\tests\__init__.py" >nul
echo ✓ Tests init copied
echo.

REM Step 8: Create .gitignore
echo Step 8: Creating configuration files...
(
    echo # Byte-compiled / optimized / DLL files
    echo __pycache__/
    echo *.py[cod]
    echo *$py.class
    echo.
    echo # Distribution
    echo build/
    echo dist/
    echo *.egg-info/
    echo.
    echo # Virtual environments
    echo venv/
    echo env/
    echo.
    echo # IDE
    echo .vscode/
    echo .idea/
    echo *.swp
    echo .DS_Store
    echo.
    echo # Testing
    echo .pytest_cache/
    echo .coverage
    echo htmlcov/
    echo.
    echo # Data and models
    echo data/
    echo models/
    echo *.csv
    echo *.pkl
    echo.
    echo # Logs
    echo logs/
    echo *.log
) > "%PROJECT_ROOT%\.gitignore"

REM Create LICENSE
(
    echo MIT License
    echo.
    echo Copyright (c) 2024 Trading AI System
    echo.
    echo Permission is hereby granted, free of charge, to any person obtaining a copy
    echo of this software and associated documentation files (the "Software"), to deal
    echo in the Software without restriction, including without limitation the rights
    echo to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    echo copies of the Software, and to permit persons to whom the Software is
    echo furnished to do so, subject to the following conditions:
    echo.
    echo The above copyright notice and this permission notice shall be included in all
    echo copies or substantial portions of the Software.
) > "%PROJECT_ROOT%\LICENSE"

echo ✓ Configuration files created
echo.

REM Summary
echo ===============================================================
echo ✅ Project structure created successfully!
echo ===============================================================
echo.
echo Next steps:
echo   1. cd %PROJECT_ROOT%
echo   2. Copy module files from uploads to trading_ai_system\*\
echo   3. pip install -e .
echo   4. python -c "import trading_ai_system; print(trading_ai_system.__version__)"
echo.
echo Project location: %cd%\%PROJECT_ROOT%
echo.
pause
