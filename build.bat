@echo off
echo ========================================
echo   CONTROLE FINANCEIRO - BUILD SCRIPT
echo ========================================
echo.

REM Limpar builds anteriores
echo [1/5] Limpando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "ControleFinanceiro.exe" del "ControleFinanceiro.exe"
echo OK!
echo.

REM Limpar cache do Python
echo [2/5] Limpando cache do Python...
for /r %%i in (*.pyc) do del "%%i" 2>nul
for /d /r %%i in (__pycache__) do rmdir /s /q "%%i" 2>nul
echo OK!
echo.

REM Verificar se PyInstaller está instalado
echo [3/5] Verificando PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller nao encontrado. Instalando...
    pip install pyinstaller
) else (
    echo PyInstaller ja instalado!
)
echo.

REM Executar PyInstaller
echo [4/5] Compilando aplicacao...
echo Isso pode levar alguns minutos...
echo.
python -m PyInstaller --clean --noconfirm ControleFinanceiro.spec
if errorlevel 1 (
    echo ERRO ao executar PyInstaller!
    echo Tentando reinstalar PyInstaller...
    pip uninstall -y pyinstaller
    pip install pyinstaller==6.5.0
    echo Tentando novamente...
    python -m PyInstaller --clean --noconfirm ControleFinanceiro.spec
)
echo.

REM Copiar config.env para a pasta dist (CRÍTICO para distribuição)
echo [5/6] Copiando config.env...
if exist "config.env" (
    copy /Y "config.env" "dist\ControleFinanceiro\config.env" >nul
    echo config.env copiado com sucesso!
) else (
    echo AVISO: config.env nao encontrado! O executavel nao funcionara sem ele.
)
echo.

REM Verificar se o build foi bem-sucedido
if exist "dist\ControleFinanceiro\ControleFinanceiro.exe" (
    echo [6/6] Build concluido com sucesso!
    echo.
    echo ========================================
    echo   EXECUTAVEL CRIADO!
    echo ========================================
    echo.
    echo Localizacao: dist\ControleFinanceiro\ControleFinanceiro.exe
    echo.
    echo Arquivos incluidos:
    echo - ControleFinanceiro.exe
    echo - config.env (credenciais Supabase)
    echo - assets/ (icones e estilos)
    echo - Bibliotecas necessarias
    echo.
    echo Voce pode:
    echo 1. Executar: dist\ControleFinanceiro\ControleFinanceiro.exe
    echo 2. Distribuir: Copie a pasta 'dist\ControleFinanceiro' completa
    echo.
    echo IMPORTANTE: O executavel precisa da pasta completa para funcionar!
    echo Nao mova apenas o .exe, mova a pasta inteira.
    echo.
) else (
    echo [6/6] ERRO: Build falhou!
    echo.
    echo Verifique os erros acima e tente novamente.
    echo.
)

pause
