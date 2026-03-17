"""Router temporário para migrar dados retroativos: criar despesas/receitas para registros existentes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.abastecimento import Abastecimento
from app.models.despesa import Despesa
from app.models.dividendo import Dividendo
from app.models.investimento import Investimento
from app.models.manutencao import Manutencao
from app.models.receita import Receita
from app.models.veiculo import Veiculo

router = APIRouter()


@router.post("/migrar-integracoes")
def migrar_integracoes(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Cria despesas/receitas retroativas para abastecimentos, manutenções, investimentos e dividendos existentes."""
    usuario_id = current_user["user_id"]
    resultado = {"abastecimentos": 0, "manutencoes": 0, "investimentos": 0, "dividendos": 0}

    # 1. Abastecimentos → Despesas
    veiculos = db.query(Veiculo).filter(Veiculo.usuario_id == usuario_id).all()
    for veiculo in veiculos:
        abastecimentos = db.query(Abastecimento).filter(Abastecimento.veiculo_id == veiculo.id).all()
        for a in abastecimentos:
            # Verificar se já existe despesa correspondente
            desc_like = f"Abastecimento - {veiculo.nome_identificador}%"
            existe = db.query(Despesa).filter(
                Despesa.usuario_id == usuario_id,
                Despesa.descricao.like(desc_like),
                Despesa.valor == a.valor,
                Despesa.data == a.data,
            ).first()
            if not existe:
                descricao = f"Abastecimento - {veiculo.nome_identificador}"
                if a.tipo:
                    descricao += f" ({a.tipo})"
                if a.posto:
                    descricao += f" - {a.posto}"
                despesa = Despesa(
                    usuario_id=usuario_id,
                    descricao=descricao,
                    valor=a.valor,
                    data=a.data,
                    pago=True,
                    data_pagamento=a.data,
                )
                db.add(despesa)
                resultado["abastecimentos"] += 1

        # 2. Manutenções → Despesas
        manutencoes = db.query(Manutencao).filter(Manutencao.veiculo_id == veiculo.id).all()
        for m in manutencoes:
            desc_like = f"Manutenção - {veiculo.nome_identificador}%"
            existe = db.query(Despesa).filter(
                Despesa.usuario_id == usuario_id,
                Despesa.descricao.like(desc_like),
                Despesa.valor == m.valor,
                Despesa.data == m.data,
            ).first()
            if not existe:
                descricao = f"Manutenção - {veiculo.nome_identificador}"
                if m.servico:
                    descricao += f" ({m.servico})"
                despesa = Despesa(
                    usuario_id=usuario_id,
                    descricao=descricao,
                    valor=m.valor,
                    data=m.data,
                    pago=True,
                    data_pagamento=m.data,
                )
                db.add(despesa)
                resultado["manutencoes"] += 1

    # 3. Investimentos → Despesas
    investimentos = db.query(Investimento).filter(Investimento.usuario_id == usuario_id).all()
    for inv in investimentos:
        desc_like = f"Investimento - {inv.nome}%"
        existe = db.query(Despesa).filter(
            Despesa.usuario_id == usuario_id,
            Despesa.descricao.like(desc_like),
            Despesa.valor == inv.valor_investido,
            Despesa.data == inv.data,
        ).first()
        if not existe:
            descricao = f"Investimento - {inv.nome}"
            if inv.tipo:
                descricao += f" ({inv.tipo})"
            despesa = Despesa(
                usuario_id=usuario_id,
                descricao=descricao,
                valor=inv.valor_investido,
                data=inv.data,
                banco_id=inv.banco_id,
                categoria_id=inv.categoria_id,
                pago=True,
                data_pagamento=inv.data,
            )
            db.add(despesa)
            resultado["investimentos"] += 1

    # 4. Dividendos → Receitas
    for inv in investimentos:
        dividendos = db.query(Dividendo).filter(Dividendo.investimento_id == inv.id).all()
        for d in dividendos:
            desc_like = f"Dividendo - {inv.nome}%"
            existe = db.query(Receita).filter(
                Receita.usuario_id == usuario_id,
                Receita.descricao.like(desc_like),
                Receita.valor == d.valor,
                Receita.data == d.data,
            ).first()
            if not existe:
                receita = Receita(
                    usuario_id=usuario_id,
                    descricao=f"Dividendo - {inv.nome}",
                    valor=d.valor,
                    data=d.data,
                    banco_id=inv.banco_id,
                    categoria_id=inv.categoria_id,
                )
                db.add(receita)
                resultado["dividendos"] += 1

    db.commit()
    return {
        "mensagem": "Migração concluída",
        "criados": resultado,
        "total": sum(resultado.values()),
    }
