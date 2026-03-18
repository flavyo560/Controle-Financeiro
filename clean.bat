@echo off
echo ========================================
echo  LIMPEZA DE ARQUIVOS DE BUILD
echo ========================================
echo.

echo Removendo pastas de build antigas...

if exist build (
    rmdir /s /q build
    echo [OK] Pasta build removida
) else (
    echo [--] Pasta build nao existe
)

if exist dist (
    rmdir /s /q dist
    echo [OK] Pasta dist removida
) else (
    echo [--] Pasta dist nao existe
)

if exist __pycache__ (
    rmdir /s /q __pycache__
    echo [OK] Cache Python removido
)

for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo.
echo ========================================
echo  LIMPEZA CONCLUIDA!
echo ========================================
echo.
echo Agora voce pode executar: build.bat
echo.
pause
