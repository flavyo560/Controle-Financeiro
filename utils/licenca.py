import json
import os
import sys
import uuid
from pathlib import Path
from datetime import date
import base64
import hashlib
from cryptography.fernet import Fernet
from dotenv import load_dotenv
try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = None

# Detectar se está rodando como executável PyInstaller
if getattr(sys, 'frozen', False):
    # Rodando como executável - buscar .env no diretório do executável
    _base_path = Path(sys.executable).parent
else:
    # Rodando como script Python - buscar .env no diretório do projeto
    _base_path = Path(__file__).resolve().parent.parent

# Tentar carregar do config.env primeiro, depois .env
_env_path = _base_path / "config.env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    # Tentar .env no diretório raiz
    _env_path = _base_path / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)

# Sempre ler de variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
_chave_raw = os.getenv("CHAVE_MESTRA")

# Validar que variáveis existem
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "ERRO: Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias.\n"
        "Configure-as no arquivo .env ou config.env, ou nas variáveis de ambiente do sistema."
    )

if not _chave_raw:
    raise ValueError(
        "ERRO: Variável de ambiente CHAVE_MESTRA é obrigatória.\n"
        "Configure-a no arquivo .env ou config.env, ou nas variáveis de ambiente do sistema."
    )

CHAVE_MESTRA = _chave_raw.encode() if _chave_raw else b""

ARQ_LICENCA = Path(os.getenv('APPDATA')) / "FinanceApp" / ".license.dat"
ARQ_LICENCA.parent.mkdir(parents=True, exist_ok=True)

def _has_master_key():
    return bool(CHAVE_MESTRA)

def _derive_key(raw: bytes) -> bytes:
    digest = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(digest)

def _get_fernet():
    if not _has_master_key():
        return None
    try:
        return Fernet(CHAVE_MESTRA)
    except Exception:
        try:
            derived = _derive_key(_chave_raw.encode())
            return Fernet(derived)
        except Exception:
            return None

def _get_supabase():
    if not create_client or not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Erro ao conectar Supabase: {e}")
        import traceback
        traceback.print_exc()
        return None

def obter_id_maquina():
    return str(uuid.getnode())

# ESSA É A FUNÇÃO QUE O APP_CONTROLLER ESTÁ PROCURANDO
def verificar_status_licenca():
    if not ARQ_LICENCA.exists(): return "NAO_ATIVADO"
    try:
        f = _get_fernet()
        if not f:
            return "ERRO"
        dados = json.loads(f.decrypt(ARQ_LICENCA.read_bytes()).decode())
        if dados["hwid_vinculado"] != obter_id_maquina(): return "PC_DIFERENTE"
        if date.today() > date.fromisoformat(dados["validade"]): return "EXPIRADA"
        return "VALIDA"
    except:
        return "ERRO"

def ativar_sistema_online(chave_digitada):
    id_pc = obter_id_maquina()
    
    # Debug: Verificar se as credenciais estão carregadas
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False, "Erro: Credenciais do Supabase não configuradas."
    
    client = _get_supabase()
    if not client:
        return False, "Erro ao conectar com servidor de ativação. Verifique sua conexão com internet."
    f = _get_fernet()
    if not f:
        return False, "Configuração ausente ou inválida: defina CHAVE_MESTRA em config.env."
    try:
        query = client.table("licencas").select("*").eq("chave", chave_digitada).execute()
        if not query.data: return False, "Chave não encontrada."
        
        licenca = query.data[0]
        if not licenca["ativa"]: return False, "Licença desativada."
        
        if licenca["hwid"] is None:
            client.table("licencas").update({"hwid": id_pc}).eq("chave", chave_digitada).execute()
        elif licenca["hwid"] != id_pc:
            return False, "Chave vinculada a outro PC."

        dados_locais = {"hwid_vinculado": id_pc, "validade": licenca["validade"], "chave": chave_digitada}
        ARQ_LICENCA.write_bytes(f.encrypt(json.dumps(dados_locais).encode()))
        return True, "Ativado com sucesso!"
    except Exception as e:
        return False, f"Erro: {str(e)}"
