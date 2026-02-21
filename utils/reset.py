import os
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox

DB_PATH = Path("financas.db")


def resetar_sistema(parent):
    resp = QMessageBox.warning(
        parent,
        "RESET GERAL",
        "⚠️ Isso apagará TODOS os dados do sistema.\n"
        "Essa ação NÃO pode ser desfeita.\n\n"
        "Deseja continuar?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )

    if resp != QMessageBox.StandardButton.Yes:
        return

    if DB_PATH.exists():
        os.remove(DB_PATH)

    QMessageBox.information(
        parent,
        "Sistema Resetado",
        "Todos os dados foram apagados.\nReinicie o aplicativo."
    )
