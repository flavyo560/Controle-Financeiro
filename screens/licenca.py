import json
from cryptography.fernet import Fernet
from datetime import date

# Use a MESMA chave que está no seu Gerador_do_Vendedor.py
CHAVE_MESTRA = b'TmBoF5NMV9bjYOoNZl5x-7dUYQOEBEkz14PkX-v7ZaE=' 
f = Fernet(CHAVE_MESTRA)

def verificar_licenca(serial_usuario):
    try:
        # 1. Descriptografa o código colado pelo cliente
        dados_brutos = f.decrypt(serial_usuario.encode()).decode()
        
        # 2. Tenta ler como JSON (formato Nome + Data)
        try:
            dados = json.loads(dados_brutos)
            data_str = dados["validade"]
            nome_cliente = dados.get("cliente", "Cliente")
        except:
            # Caso você ainda tenha chaves antigas que eram só a data
            data_str = dados_brutos
            nome_cliente = "Usuário"

        # 3. Compara a data
        data_validade = date.fromisoformat(data_str)
        
        if data_validade >= date.today():
            return True, f"Olá {nome_cliente}, sua licença é válida até {data_validade.strftime('%d/%m/%Y')}."
        else:
            return False, "Sua licença expirou. Entre em contato com o suporte."
            
    except Exception:
        return False, "Chave de ativação inválida ou corrompida."