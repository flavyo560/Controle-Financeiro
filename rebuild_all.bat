@echo off
echo ========================================
echo   REBUILD COMPLETO - EXE + INSTALADOR
echo ========================================
echo.

echo [1/2] Compilando executavel...
call build.bat
if errorlevel 1 (
    echo ERRO ao compilar executavel!
    pause
    exit /b 1
)

echo.
echo [2/2] Compilando instalador...
call build_installer.bat
if errorlevel 1 (
    echo ERRO ao compilar instalador!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   REBUILD COMPLETO COM SUCESSO!
echo ========================================
echo.
pause
