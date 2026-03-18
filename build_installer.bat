@echo off
echo ========================================
echo   CRIAR INSTALADOR - INNO SETUP
echo ========================================
echo.

REM Verificar se o Inno Setup está instalado
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist %INNO_PATH% (
    echo ERRO: Inno Setup nao encontrado!
    echo.
    echo Por favor, instale o Inno Setup 6:
    echo https://jrsoftware.org/isdl.php
    echo.
    pause
    exit /b 1
)

REM Verificar se a pasta dist existe
if not exist "dist\ControleFinanceiro" (
    echo ERRO: Pasta dist\ControleFinanceiro nao encontrada!
    echo.
    echo Execute primeiro: .\build.bat
    echo.
    pause
    exit /b 1
)

REM Compilar o instalador
echo Compilando instalador...
echo.
%INNO_PATH% installer.iss

if errorlevel 1 (
    echo.
    echo ERRO: Falha ao compilar o instalador!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   INSTALADOR CRIADO COM SUCESSO!
echo ========================================
echo.
echo Arquivo: Instalador_ControleFinanceiro_v2.3.exe
echo.
echo Voce pode distribuir este arquivo para seus usuarios.
echo.
pause
