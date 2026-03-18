import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setToken(token: string): void {
  localStorage.setItem("token", token);
  document.cookie = `token=${token}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
}

export function removeToken(): void {
  localStorage.removeItem("token");
  document.cookie = "token=; path=/; max-age=0; path=/";
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export async function login(identificador: string, senha: string) {
  const { data } = await axios.post(`${API_URL}/auth/login`, { identificador, senha });
  setToken(data.access_token);
  return data;
}
