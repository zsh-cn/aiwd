@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ========================================
echo   AI Doc Batch Generator - PyInstaller Build
echo ========================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python and add to PATH.
    pause
    exit /b 1
)

echo [INFO] Installing project dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Installing PyInstaller...
    python -m pip install pyinstaller
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

pyinstaller --noconfirm --clean --onefile --windowed --name "AI_Doc_Generator" --paths "%cd%" --hidden-import config --hidden-import api_client --hidden-import title_generator --hidden-import doc_generator --hidden-import converter --hidden-import ui --hidden-import ui.main_window --hidden-import ui.settings_dialog --hidden-import ui.widgets --hidden-import utils --hidden-import utils.file_utils --hidden-import utils.prompt_templates --hidden-import pypandoc --collect-all httpx --collect-all pypandoc_binary main.py

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