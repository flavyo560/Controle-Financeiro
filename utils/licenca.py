import json
import os
import uuid
from pathlib import Path
from datetime import date
from cryptography.fernet import Fernet
from supabase import create_client, Client

# --- CONFIGURAÇÕES DO SUPABASE ---
SUPABASE_URL = "https://gflqjkwrqagxexhhwtih.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdmbHFqa3dycWFneGV4aGh3dGloIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE2MDQzMzksImV4cCI6MjA4NzE4MDMzOX0.4WslVZ0TDccDJpwCvrgmv_KtMLhsHIbyEvjcIclEZbM"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CHAVE_MESTRA = b'TmBoF5NMV9bjYOoNZl5x-7dUYQOEBEkz14PkX-v7ZaE='
ARQ_LICENCA = Path(os.getenv('APPDATA')) / "FinanceApp" / ".license.dat"
ARQ_LICENCA.parent.mkdir(parents=True, exist_ok=True)

def obter_id_maquina():
    return str(uuid.getnode())

# ESSA É A FUNÇÃO QUE O APP_CONTROLLER ESTÁ PROCURANDO
def verificar_status_licenca():
    if not ARQ_LICENCA.exists(): return "NAO_ATIVADO"
    try:
        f = Fernet(CHAVE_MESTRA)
        dados = json.loads(f.decrypt(ARQ_LICENCA.read_bytes()).decode())
        if dados["hwid_vinculado"] != obter_id_maquina(): return "PC_DIFERENTE"
        if date.today() > date.fromisoformat(dados["validade"]): return "EXPIRADA"
        return "VALIDA"
    except:
        return "ERRO"

def ativar_sistema_online(chave_digitada):
    id_pc = obter_id_maquina()
    try:
        query = supabase.table("licencas").select("*").eq("chave", chave_digitada).execute()
        if not query.data: return False, "Chave não encontrada."
        
        licenca = query.data[0]
        if not licenca["ativa"]: return False, "Licença desativada."
        
        if licenca["hwid"] is None:
            supabase.table("licencas").update({"hwid": id_pc}).eq("chave", chave_digitada).execute()
        elif licenca["hwid"] != id_pc:
            return False, "Chave vinculada a outro PC."

        f = Fernet(CHAVE_MESTRA)
        dados_locais = {"hwid_vinculado": id_pc, "validade": licenca["validade"], "chave": chave_digitada}
        ARQ_LICENCA.write_bytes(f.encrypt(json.dumps(dados_locais).encode()))
        return True, "Ativado com sucesso!"
    except Exception as e:
        return False, f"Erro: {str(e)}"