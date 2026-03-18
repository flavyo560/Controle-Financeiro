"""Script para migrar dados retroativos via API."""
import requests

BASE = "https://controle-financeiro-wd04.onrender.com/api/v1"

# Login
login = requests.post(f"{BASE}/auth/login", json={"identificador": "teste@teste.com", "senha": "teste12345"}, timeout=120)
print("Login status:", login.status_code)
if login.status_code != 200:
    print("Erro:", login.text)
    exit(1)

token = login.json().get("access_token")
print("Token obtido")

# Migrar
resp = requests.post(f"{BASE}/migrar/migrar-integracoes", headers={"Authorization": f"Bearer {token}"}, timeout=120)
print("Migracao status:", resp.status_code)
print("Resposta:", resp.text)
