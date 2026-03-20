"""Script para atualizar senha do admin e remover usuario teste."""
from sqlalchemy import create_engine, text
import bcrypt

engine = create_engine(
    "postgresql://postgres.eyhnjyjcgjwstjekxaqx:2G00MQ55bWb0VGe9"
    "@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
)

new_senha = "030414"
senha_hash = bcrypt.hashpw(new_senha.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

with engine.connect() as conn:
    # Atualizar senha do admin (id=3)
    conn.execute(
        text("UPDATE usuarios SET senha_hash_bcrypt = :senha, senha_hash = NULL WHERE id = 3"),
        {"senha": senha_hash},
    )
    conn.commit()
    print("Senha do admin atualizada!")

    # Listar tabelas para encontrar nome correto
    result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"))
    tables = [r[0] for r in result.fetchall()]
    print(f"Tabelas: {tables}")

    # Deletar dados do usuario teste (id=4)
    for t in tables:
        try:
            conn.execute(text(f"DELETE FROM {t} WHERE usuario_id = 4"))
        except Exception:
            conn.rollback()
    conn.commit()

    try:
        conn.execute(text("DELETE FROM usuarios WHERE id = 4"))
        conn.commit()
        print("Usuario teste removido!")
    except Exception as e:
        conn.rollback()
        print(f"Nao conseguiu remover teste: {e}")

    result = conn.execute(text("SELECT id, nome, email, perfil FROM usuarios ORDER BY id"))
    for r in result.fetchall():
        print(f"id={r[0]}, nome={r[1]}, email={r[2]}, perfil={r[3]}")
