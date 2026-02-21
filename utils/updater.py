import requests
import os
import subprocess
import sys
import urllib.request
from PyQt6.QtWidgets import QMessageBox

# Substitua pelos seus links reais do GitHub
VERSION_URL = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/version.txt"
INSTALLER_URL = "https://github.com/SEU_USUARIO/SEU_REPO/releases/latest/download/Instalador_Financeiro_V2_3.exe"
VERSION_ATUAL = "2.3"

def verificar_e_atualizar(parent):
    try:
        response = requests.get(VERSION_URL, timeout=5)
        if response.status_code == 200:
            versao_remota = response.text.strip()
            
            if versao_remota > VERSION_ATUAL:
                msg = QMessageBox.question(
                    parent, "Atualização disponível!",
                    f"A versão {versao_remota} está disponível. Deseja atualizar agora?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if msg == QMessageBox.StandardButton.Yes:
                    # Caminho temporário para baixar o instalador
                    temp_exe = os.path.join(os.getenv("TEMP"), "update_setup.exe")
                    urllib.request.urlretrieve(INSTALLER_URL, temp_exe)
                    
                    # Roda o instalador e fecha o app atual
                    # O parâmetro /SILENT faz a instalação automática
                    subprocess.Popen([temp_exe, "/SILENT", "/CLOSEAPPLICATIONS"])
                    sys.exit()
    except Exception as e:
        print(f"Erro ao verificar atualização: {e}")