@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ========================================
echo   AI Doc Batch Generator - PyInstaller Build
echo ========================================
echo.

set "VENV_DIR=.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"
set "VENV_PYINSTALLER=%VENV_DIR%\Scripts\pyinstaller.exe"

if not exist "%VENV_PYTHON%" (
    echo [INFO] Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created.
    echo.
)

echo [INFO] Upgrading pip...
"%VENV_PYTHON%" -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/
if %errorlevel% neq 0 (
    echo [ERROR] Failed to upgrade pip.
    pause
    exit /b 1
)

echo [INFO] Installing project dependencies...
"%VENV_PIP%" install -i https://pypi.tuna.tsinghua.edu.cn/simple/ -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

"%VENV_PYTHON%" -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Installing PyInstaller...
    "%VENV_PIP%" install -i https://pypi.tuna.tsinghua.edu.cn/simple/ pyinstaller
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "AI_Doc_Generator.spec" del /q "AI_Doc_Generator.spec"

echo [INFO] Building executable...
echo.

"%VENV_PYINSTALLER%" --noconfirm --clean --onefile --windowed --name "AI_Doc_Generator" --paths "%cd%" --hidden-import config --hidden-import api_client --hidden-import title_generator --hidden-import doc_generator --hidden-import converter --hidden-import ui --hidden-import ui.main_window --hidden-import ui.settings_dialog --hidden-import ui.widgets --hidden-import utils --hidden-import utils.file_utils --hidden-import utils.prompt_templates --hidden-import pypandoc --collect-all httpx --collect-all pypandoc main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed! Check the log above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build successful!
echo   Executable: dist\AI_Doc_Generator.exe
echo ========================================
echo.
pause
endlocal