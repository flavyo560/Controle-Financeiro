@echo off
echo Limpando cache do Python...
echo.

REM Remover arquivos .pyc
echo Removendo arquivos .pyc...
for /r %%i in (*.pyc) do (
    del "%%i"
    echo Removido: %%i
)

REM Remover diretórios __pycache__
echo.
echo Removendo diretórios __pycache__...
for /d /r %%i in (__pycache__) do (
    rmdir /s /q "%%i"
    echo Removido: %%i
)

echo.
echo Cache limpo com sucesso!
echo Agora feche completamente o aplicativo e execute novamente.
echo.
pause
