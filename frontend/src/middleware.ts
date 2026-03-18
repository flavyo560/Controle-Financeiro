import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login", "/cadastro"];
const RESTRICTED_PATHS = ["/frota", "/investimentos", "/orcamento", "/cartoes"];
const ADMIN_PATHS = ["/admin"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Allow static files and API routes
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Check for auth token in cookies
  const token = request.cookies.get("access_token")?.value;

  if (!token) {
    const authHeader = request.headers.get("authorization");
    if (!authHeader) {
      const loginUrl = new URL("/login", request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  // If token exists, try to check expiration and extract plan/profile
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const expiry = payload.exp * 1000;
      if (Date.now() >= expiry) {
        const response = NextResponse.redirect(new URL("/login", request.url));
        response.cookies.delete("access_token");
        return response;
      }

      const perfil = payload.perfil || "";
      const plano = payload.plano || "";

      // Admin route protection
      if (ADMIN_PATHS.some((p) => pathname.startsWith(p))) {
        if (perfil !== "admin") {
          return NextResponse.redirect(new URL("/dashboard", request.url));
        }
      }

      // Restricted module route protection
      if (RESTRICTED_PATHS.some((p) => pathname.startsWith(p))) {
        if (perfil !== "admin" && plano !== "plus") {
          return NextResponse.redirect(new URL("/planos", request.url));
        }
      }
    } catch {
      // Invalid token format, redirect to login
      const response = NextResponse.redirect(new URL("/login", request.url));
      response.cookies.delete("access_token");
      return response;
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
