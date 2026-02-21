import json
from pathlib import Path
from datetime import datetime, timedelta

TRIAL_PATH = Path(__file__).resolve().parent.parent / "data" / "trial.json"


def iniciar_trial():
    TRIAL_PATH.parent.mkdir(exist_ok=True)

    inicio = datetime.now()
    fim = inicio + timedelta(days=7)

    dados = {
        "trial_inicio": inicio.strftime("%Y-%m-%d"),
        "trial_fim": fim.strftime("%Y-%m-%d"),
        "expirado": False
    }

    with open(TRIAL_PATH, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)


def carregar_trial():
    if not TRIAL_PATH.exists():
        iniciar_trial()

    with open(TRIAL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def trial_expirado():
    dados = carregar_trial()
    hoje = datetime.now().date()
    fim = datetime.strptime(dados["trial_fim"], "%Y-%m-%d").date()

    if hoje > fim:
        dados["expirado"] = True
        with open(TRIAL_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4)
        return True

    return False
