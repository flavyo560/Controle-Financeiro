@echo off
cls
echo ========================================
echo  CRIAR INSTALADOR - INNO SETUP
echo ========================================
echo.

REM Verificar se o executável existe
if not exist "dist\ControleFinanceiro.exe" (
    echo ERRO: Executavel nao encontrado!
    echo.
    echo Execute primeiro: BUILD_PRODUCAO.bat
    echo.
    pause
    exit /b 1
)

echo [OK] Executavel encontrado
echo.

REM Criar pasta para o instalador
if not exist "installer" mkdir installer

REM Verificar se Inno Setup está instalado
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist %INNO_PATH% (
    echo.
    echo AVISO: Inno Setup nao encontrado!
    echo.
    echo Por favor:
    echo 1. Baixe Inno Setup de: https://jrsoftware.org/isdl.php
    echo 2. Instale o Inno Setup
    echo 3. Execute este script novamente
    echo.
    echo OU compile manualmente:
    echo 1. Abra o Inno Setup
    echo 2. Abra o arquivo: instalador.iss
    echo 3. Clique em Build ^> Compile
    echo.
    pause
    exit /b 1
)

echo [OK] Inno Setup encontrado
echo.

echo Compilando instalador...
echo.

%INNO_PATH% instalador.iss

if %errorlevel% neq 0 (
    echo.
    echo ERRO ao compilar instalador
    pause
    exit /b 1
)

echo.
echo ========================================
echo  INSTALADOR CRIADO COM SUCESSO!
echo ========================================
echo.

if exist "installer\Instalador_Controle_Financeiro_v2.4.exe" (
    echo Instalador criado: installer\Instalador_Controle_Financeiro_v2.4.exe
    echo.
    echo Pronto para distribuir!
) else (
    echo AVISO: Instalador nao encontrado em installer\
)

echo.
pause
