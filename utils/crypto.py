from cryptography.fernet import Fernet
from pathlib import Path

# Pasta segura do app
PASTA_DADOS = Path.home() / ".finapp"
PASTA_DADOS.mkdir(exist_ok=True)

ARQUIVO_CHAVE = PASTA_DADOS / "key.key"


# ==============================
# 🔑 CHAVE
# ==============================
def obter_chave():
    if not ARQUIVO_CHAVE.exists():
        chave = Fernet.generate_key()
        ARQUIVO_CHAVE.write_bytes(chave)
    return ARQUIVO_CHAVE.read_bytes()


# ==============================
# 🔐 CRIPTOGRAFIA
# ==============================
def criptografar_arquivo(arquivo: Path):
    if not arquivo.exists():
        return

    fernet = Fernet(obter_chave())
    dados = arquivo.read_bytes()
    dados_criptografados = fernet.encrypt(dados)

    arquivo.with_suffix(arquivo.suffix + ".enc").write_bytes(dados_criptografados)
    arquivo.unlink()  # remove original


def descriptografar_arquivo(arquivo_enc: Path):
    if not arquivo_enc.exists():
        return

    fernet = Fernet(obter_chave())
    dados = arquivo_enc.read_bytes()
    dados_descriptografados = fernet.decrypt(dados)

    original = arquivo_enc.with_suffix("")
    original.write_bytes(dados_descriptografados)
    arquivo_enc.unlink()
