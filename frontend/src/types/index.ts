// ============================================================
// TypeScript interfaces para todas as entidades do sistema
// Mapeamento direto das 20+ tabelas do backend
// ============================================================

// --- Usuário ---

export interface Usuario {
  id: number;
  nome: string;
  email: string;
  cpf?: string | null;
  telefone?: string | null;
  perfil: string;
  criado_em: string;
}

// --- Banco ---

export interface Banco {
  id: number;
  usuario_id: number;
  nome: string;
  saldo_inicial: number;
  ativo: boolean;
  criado_em: string;
  saldo_calculado?: number;
}

export interface BancoCreate {
  nome: string;
  saldo_inicial?: number;
}

// --- Categoria ---

export interface Categoria {
  id: number;
  usuario_id: number;
  nome: string;
  tipo: "receita" | "despesa";
  ativo: boolean;
  criado_em: string;
}

export interface CategoriaCreate {
  nome: string;
  tipo: "receita" | "despesa";
}

// --- Receita ---

export interface Receita {
  id: number;
  usuario_id: number;
  descricao?: string | null;
  valor: number;
  data: string;
  categoria_id?: number | null;
  banco_id?: number | null;
  ativo: boolean;
  categoria?: Categoria | null;
  banco?: Banco | null;
}

export interface ReceitaCreate {
  descricao?: string;
  valor: number;
  data: string;
  categoria_id?: number;
  banco_id?: number;
}

// --- Despesa ---

export interface Despesa {
  id: number;
  usuario_id: number;
  descricao?: string | null;
  valor: number;
  data: string;
  categoria_id?: number | null;
  banco_id?: number | null;
  pago: boolean;
  data_vencimento?: string | null;
  data_pagamento?: string | null;
  parcela_numero?: number | null;
  parcela_total?: number | null;
  despesa_parcelada_id?: number | null;
  despesa_recorrente_id?: number | null;
  cartao_id?: number | null;
  mes_fatura?: string | null;
  ativo: boolean;
  categoria?: Categoria | null;
  banco?: Banco | null;
}

export interface DespesaCreate {
  descricao?: string;
  valor: number;
  data: string;
  categoria_id?: number;
  banco_id?: number;
  data_vencimento?: string;
}

// --- Despesa Parcelada ---

export interface DespesaParcelada {
  id: number;
  usuario_id: number;
  descricao: string;
  valor_total: number;
  numero_parcelas: number;
  data_primeira_parcela: string;
  categoria_id?: number | null;
  banco_id?: number | null;
  criado_em: string;
  despesas?: Despesa[];
}

export interface DespesaParceladaCreate {
  descricao: string;
  valor_total: number;
  numero_parcelas: number;
  data_primeira_parcela: string;
  categoria_id?: number;
  banco_id?: number;
}

// --- Despesa Recorrente ---

export interface DespesaRecorrente {
  id: number;
  usuario_id: number;
  descricao: string;
  valor: number;
  dia_mes: number;
  categoria_id?: number | null;
  banco_id?: number | null;
  data_inicio: string;
  data_fim?: string | null;
  ativa: boolean;
  criado_em: string;
}

export interface DespesaRecorrenteCreate {
  descricao: string;
  valor: number;
  dia_mes: number;
  categoria_id?: number;
  banco_id?: number;
  data_inicio: string;
  data_fim?: string;
}

// --- Cartão de Crédito ---

export interface Cartao {
  id: number;
  usuario_id: number;
  nome: string;
  bandeira?: string | null;
  limite_total: number;
  dia_fechamento: number;
  dia_vencimento: number;
  status: boolean;
  criado_em: string;
  limite_utilizado?: number;
  limite_disponivel?: number;
}

export interface CartaoCreate {
  nome: string;
  bandeira?: string;
  limite_total: number;
  dia_fechamento: number;
  dia_vencimento: number;
}

// --- Compra no Cartão ---

export interface CompraCartao {
  id: number;
  cartao_id: number;
  descricao: string;
  valor: number;
  data_compra: string;
  categoria_id?: number | null;
  mes_fatura: string;
  parcela_atual?: number | null;
  total_parcelas?: number | null;
  compra_parcelada_id?: number | null;
  criado_em: string;
  categoria?: Categoria | null;
}

export interface CompraCartaoCreate {
  descricao: string;
  valor: number;
  data_compra: string;
  categoria_id?: number;
}

export interface CompraParceladaCreate {
  descricao: string;
  valor_total: number;
  numero_parcelas: number;
  data_compra: string;
  categoria_id?: number;
}

// --- Pagamento de Fatura ---

export interface PagamentoFatura {
  id: number;
  cartao_id: number;
  mes_fatura: string;
  valor_pago: number;
  data_pagamento: string;
  banco_id: number;
  despesa_id?: number | null;
  criado_em: string;
}

export interface PagamentoFaturaCreate {
  valor_pago: number;
  data_pagamento: string;
  banco_id: number;
}

// --- Fatura ---

export interface Fatura {
  mes_fatura: string;
  compras: CompraCartao[];
  valor_total: number;
  valor_pago: number;
  saldo_devedor: number;
  data_vencimento: string;
  status: "pendente" | "paga_parcial" | "paga_total" | "vencida";
}

// --- Investimento ---

export interface Investimento {
  id: number;
  usuario_id: number;
  nome: string;
  tipo?: string | null;
  valor_investido: number;
  valor_atual?: number | null;
  data: string;
  ativo: boolean;
  categoria_id?: number | null;
  banco_id?: number | null;
  criado_em: string;
  rentabilidade?: number;
}

export interface InvestimentoCreate {
  nome: string;
  tipo?: string;
  valor_investido: number;
  valor_atual?: number;
  data: string;
  categoria_id?: number;
  banco_id?: number;
}

// --- Dividendo ---

export interface Dividendo {
  id: number;
  investimento_id: number;
  valor: number;
  data: string;
}

export interface DividendoCreate {
  valor: number;
  data: string;
}

// --- Transferência ---

export interface Transferencia {
  id: number;
  usuario_id: number;
  banco_origem_id?: number | null;
  banco_destino_id?: number | null;
  valor: number;
  data: string;
  descricao?: string | null;
  banco_origem?: Banco | null;
  banco_destino?: Banco | null;
}

export interface TransferenciaCreate {
  banco_origem_id: number;
  banco_destino_id: number;
  valor: number;
  data: string;
  descricao?: string;
}

// --- Veículo ---

export interface Veiculo {
  id: number;
  usuario_id: number;
  nome_identificador: string;
  placa?: string | null;
  modelo?: string | null;
  status: boolean;
}

export interface VeiculoCreate {
  nome_identificador: string;
  placa?: string;
  modelo?: string;
}

// --- Abastecimento ---

export interface Abastecimento {
  id: number;
  veiculo_id: number;
  data: string;
  litros?: number | null;
  valor: number;
  km?: number | null;
  posto?: string | null;
  tipo?: string | null;
  litros_gasolina?: number | null;
  litros_etanol?: number | null;
}

export interface AbastecimentoCreate {
  data: string;
  litros?: number;
  valor: number;
  km?: number;
  posto?: string;
  tipo?: string;
  litros_gasolina?: number;
  litros_etanol?: number;
}

// --- Manutenção ---

export interface Manutencao {
  id: number;
  veiculo_id: number;
  data: string;
  servico?: string | null;
  valor: number;
  km?: number | null;
}

export interface ManutencaoCreate {
  data: string;
  servico?: string;
  valor: number;
  km?: number;
}

// --- Orçamento ---

export interface Orcamento {
  id: number;
  usuario_id: number;
  ano: number;
  status: "ativo" | "inativo";
  criado_em: string;
  atualizado_em: string;
}

export interface OrcamentoCreate {
  ano: number;
}

// --- Item de Orçamento ---

export interface ItemOrcamento {
  id: number;
  orcamento_id: number;
  categoria_id: number;
  mes: number;
  valor_planejado: number;
  criado_em: string;
  atualizado_em: string;
  categoria?: Categoria | null;
  valor_realizado?: number;
  percentual_execucao?: number;
}

export interface ItemOrcamentoCreate {
  categoria_id: number;
  mes: number;
  valor_planejado: number;
}

// --- Histórico de Orçamento ---

export interface HistoricoOrcamento {
  id: number;
  item_orcamento_id: number;
  data_alteracao: string;
  valor_anterior: number;
  valor_novo: number;
  usuario_id?: number | null;
}

// --- Configuração ---

export interface Configuracao {
  id: number;
  usuario_id: number;
  chave: string;
  valor?: string | null;
}

export interface ConfiguracaoCreate {
  chave: string;
  valor?: string;
}

// ============================================================
// Tipos auxiliares para API responses
// ============================================================

// --- Paginação ---

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// --- Auth ---

export interface LoginRequest {
  identificador: string;
  senha: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: Usuario;
}

export interface RegisterRequest {
  nome: string;
  email: string;
  senha: string;
  cpf?: string;
  telefone?: string;
}

// --- Dashboard ---

export interface DashboardResponse {
  patrimonio_total: number;
  saldos_bancos: { banco: Banco; saldo: number }[];
  resumo_mensal: {
    total_receitas: number;
    total_despesas: number;
    saldo: number;
  };
  alertas: {
    despesas_vencidas: Despesa[];
    despesas_vencendo: Despesa[];
  };
}

export interface DespesasPorCategoria {
  categoria: string;
  valor: number;
  percentual: number;
}

export interface EvolucaoMensal {
  mes: string;
  receitas: number;
  despesas: number;
  saldo: number;
}

// --- Relatórios ---

export interface RelatorioMensal {
  mes: number;
  ano: number;
  total_receitas: number;
  total_despesas: number;
  saldo: number;
  despesas_por_categoria: { categoria: string; valor: number }[];
  receitas_por_categoria: { categoria: string; valor: number }[];
}

export interface RelatorioAnual {
  ano: number;
  meses: {
    mes: number;
    receitas: number;
    despesas: number;
    saldo: number;
  }[];
}

export interface RelatorioVeiculo {
  veiculo: Veiculo;
  custo_abastecimento: number;
  custo_manutencao: number;
  custo_total: number;
  consumo_medio: number;
  custo_por_km: number;
}

// --- Orçamento Análise ---

export interface ProjecaoOrcamento {
  categoria: string;
  valor_realizado: number;
  projecao_anual: number;
  valor_planejado_anual: number;
  risco_estouro: boolean;
}

export interface SugestaoOrcamento {
  categoria: string;
  tipo: "acima" | "abaixo";
  percentual_medio: number;
  sugestao: string;
}

export interface TotaisMensais {
  mes: number;
  planejado_receitas: number;
  planejado_despesas: number;
  realizado_receitas: number;
  realizado_despesas: number;
  saldo_planejado: number;
  saldo_realizado: number;
}
