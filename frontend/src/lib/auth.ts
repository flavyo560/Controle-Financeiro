import api from "./api";

const TOKEN_KEY = "token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export async function login(
  identificador: string,
  senha: string
): Promise<{ access_token: string; user: Record<string, unknown> }> {
  const response = await api.post("/auth/login", { identificador, senha });
  return response.data;
}
