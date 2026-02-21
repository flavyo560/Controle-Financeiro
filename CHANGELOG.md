🚀 Adicionado
Módulo de Dividendos: Nova tela para registro de proventos vinculados a ativos específicos.

Cálculo de Rentabilidade Real (Total Return): A performance agora soma a valorização de mercado mais os dividendos acumulados.

Atualização de Saldo (Marcação a Mercado): Tela dedicada para atualizar o preço atual de títulos do Tesouro e Ações sem alterar o custo de aquisição.

Botão de Exclusão: Funcionalidade para remover lançamentos de dividendos incorretos com estorno automático no fluxo de caixa.

Persistência de Dados: Nova lógica de banco de dados para separar Valor Investido de Valor Atual.

🛠️ Corrigido
Bug de Sobrescrita: Corrigido erro onde a atualização de preço apagava o valor original de compra.

Dependências de Compilação: Resolvido erro ModuleNotFoundError: cryptography ao empacotar o sistema com múltiplos ambientes Python.

Estorno de Receitas: Agora, ao excluir um dividendo, o lançamento correspondente na tabela de receitas também é removido.

🎨 Interface e UX
Inicialização Maximizada: O sistema agora inicia automaticamente em tela cheia para melhor visualização dos dados.

Sincronização em Tempo Real: Implementação de sinais para atualizar tabelas de rentabilidade instantaneamente após novos lançamentos.

Visual Neon Dinâmico: Melhoria no contraste das tabelas com realce de cores para lucros (verde) e prejuízos (vermelho).