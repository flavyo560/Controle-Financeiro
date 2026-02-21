import json
import hashlib
import uuid
from pathlib import Path
from datetime import date, timedelta

SEGREDO_APP = "FINANCE_APP_2025_SEGREDO"
ARQ_LICENCA = Path.home() / ".finance_app_licenca.json"


def obter_id_maquina():
    return str(uuid.getnode())


def gerar_chave(id_maquina, validade):
    base = f"{id_maquina}|{validade}|{SEGREDO_APP}"
    return hashlib.sha256(base.encode()).hexdigest()


def criar_trial(dias=7):
    validade = (date.today() + timedelta(days=dias)).isoformat()
    chave = gerar_chave(obter_id_maquina(), validade)

    dados = {
        "chave": chave,
        "validade": validade,
        "trial": True
    }

    ARQ_LICENCA.write_text(json.dumps(dados))


def licenca_valida():
    if not ARQ_LICENCA.exists():
        criar_trial()
        return True

    dados = json.loads(ARQ_LICENCA.read_text())

    if date.today() > date.fromisoformat(dados["validade"]):
        return False

    chave_esperada = gerar_chave(
        obter_id_maquina(),
        dados["validade"]
    )

    return dados["chave"] == chave_esperada
