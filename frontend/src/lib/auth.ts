import api from "./api";

const TOKEN_KEY = "token";
const COOKIE_NAME = "access_token";

function setCookie(name: string, value: string, days: number): void {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function deleteCookie(name: string): void {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax`;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
  setCookie(COOKIE_NAME, token, 1);
}

export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  deleteCookie(COOKIE_NAME);
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
