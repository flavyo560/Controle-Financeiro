"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import { useSubscriptionStore } from "@/stores/subscriptionStore";
import UpgradeModal from "@/components/subscription/UpgradeModal";

const RESTRICTED_HREFS = ["/cartoes", "/investimentos", "/frota", "/orcamento"];

const navLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/bancos", label: "Bancos" },
  { href: "/categorias", label: "Categorias" },
  { href: "/lancamentos/despesas", label: "Despesas" },
  { href: "/lancamentos/receitas", label: "Receitas" },
  { href: "/lancamentos/transferencias", label: "Transferências" },
  { href: "/cartoes", label: "Cartões" },
  { href: "/investimentos", label: "Investimentos" },
  { href: "/frota", label: "Frota" },
  { href: "/orcamento", label: "Orçamento" },
  { href: "/relatorios/mensal", label: "Relatórios" },
  { href: "/ferramentas", label: "Ferramentas" },
  { href: "/planos", label: "Planos" },
  { href: "/perfil", label: "Perfil" },
];

export default function Sidebar() {
  const [open, setOpen] = useState(false);
  const [upgradeModule, setUpgradeModule] = useState<string | null>(null);
  const pathname = usePathname();
  const router = useRouter();
  const { user, clearAuth } = useAuthStore();
  const { hasAccess } = useSubscriptionStore();

  const isAdmin = user?.perfil === "admin";

  function handleLogout() {
    clearAuth();
    setOpen(false);
    router.push("/login");
  }

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  const isRestricted = (href: string) => {
    if (isAdmin) return false;
    if (!RESTRICTED_HREFS.includes(href)) return false;
    const modulo = href.replace("/", "");
    return !hasAccess(modulo);
  };

  return (
    <div className="md:hidden">
      {/* Hamburger button */}
      <button
        onClick={() => setOpen(true)}
        className="fixed top-3 left-3 z-50 p-2 rounded-lg bg-surface border border-border text-foreground"
        aria-label="Abrir menu"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Overlay */}
      {open && (
        <div className="fixed inset-0 z-50 bg-black/60" onClick={() => setOpen(false)} />
      )}

      {/* Sidebar panel */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-surface border-r border-border transform transition-transform duration-200 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-border">
          <span className="text-accent font-bold text-lg">CF</span>
          <button
            onClick={() => setOpen(false)}
            className="p-1 text-foreground hover:text-accent"
            aria-label="Fechar menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <nav className="flex flex-col p-2 gap-1">
          {navLinks.map((link) => {
            const restricted = isRestricted(link.href);

            if (restricted) {
              return (
                <button
                  key={link.href}
                  onClick={() => {
                    setOpen(false);
                    setUpgradeModule(link.label);
                  }}
                  className="px-4 py-2.5 rounded-lg text-sm transition-colors text-muted/50 text-left flex items-center gap-2"
                >
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  {link.label}
                </button>
              );
            }

            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className={`px-4 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive(link.href)
                    ? "bg-accent/10 text-accent border-l-2 border-accent"
                    : "text-foreground hover:bg-surface-hover hover:text-accent"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
          {isAdmin && (
            <Link
              href="/admin/usuarios"
              onClick={() => setOpen(false)}
              className={`px-4 py-2.5 rounded-lg text-sm transition-colors ${
                pathname.startsWith("/admin")
                  ? "bg-accent/10 text-accent border-l-2 border-accent"
                  : "text-foreground hover:bg-surface-hover hover:text-accent"
              }`}
            >
              Admin
            </Link>
          )}
          <div className="border-t border-border mt-2 pt-2">
            <button
              onClick={handleLogout}
              className="w-full px-4 py-2.5 rounded-lg text-sm transition-colors text-red-400 hover:bg-red-400/10 text-left"
            >
              Sair
            </button>
          </div>
        </nav>
      </aside>

      <UpgradeModal
        isOpen={!!upgradeModule}
        onClose={() => setUpgradeModule(null)}
        moduleName={upgradeModule ?? ""}
      />
    </div>
  );
}
