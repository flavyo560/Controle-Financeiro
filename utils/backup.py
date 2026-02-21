import shutil
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox

# caminho real do banco
DB_PATH = Path(__file__).resolve().parent.parent / "financas.db"


def realizar_backup(parent):
    destino, _ = QFileDialog.getSaveFileName(
        parent,
        "Salvar Backup",
        "backup_financas.db",
        "Banco de Dados (*.db)"
    )

    if not destino:
        return

    try:
        shutil.copy(DB_PATH, destino)
        QMessageBox.information(
            parent,
            "Backup",
            "Backup realizado com sucesso!"
        )
    except Exception as e:
        QMessageBox.critical(
            parent,
            "Erro",
            f"Erro ao realizar backup:\n{e}"
        )


def restaurar_backup(parent):
    origem, _ = QFileDialog.getOpenFileName(
        parent,
        "Restaurar Backup",
        "",
        "Banco de Dados (*.db)"
    )

    if not origem:
        return

    resp = QMessageBox.question(
        parent,
        "Confirmar Restauração",
        "⚠️ Restaurar o backup irá SUBSTITUIR todos os dados atuais.\n\n"
        "Deseja continuar?"
    )

    if resp != QMessageBox.StandardButton.Yes:
        return

    try:
        shutil.copy(origem, DB_PATH)
        QMessageBox.information(
            parent,
            "Backup Restaurado",
            "Backup restaurado com sucesso.\n\n"
            "➡️ Reinicie o aplicativo para aplicar as alterações."
        )
    except Exception as e:
        QMessageBox.critical(
            parent,
            "Erro",
            f"Erro ao restaurar backup:\n{e}"
        )
