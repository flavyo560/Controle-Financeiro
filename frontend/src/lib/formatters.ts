export function formatCurrency(value: number | string | null | undefined): string {
  if (value == null) return "R$ 0,00";
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number(value));
}

export function formatDate(date: string | null | undefined): string {
  if (!date) return "-";
  return new Intl.DateTimeFormat("pt-BR").format(new Date(date));
}

export function formatDateTime(date: string | null | undefined): string {
  if (!date) return "-";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(date));
}

export function formatPercent(value: number | string | null | undefined): string {
  if (value == null) return "0%";
  return `${Number(value).toFixed(2)}%`;
}

export function formatDecimal(value: number | string | null | undefined, decimals = 2): string {
  if (value == null) return "0";
  return Number(value).toFixed(decimals).replace(".", ",");
}
