"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
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

export default function Navbar() {
  const pathname = usePathname();
  const { user } = useAuthStore();
  const { hasAccess } = useSubscriptionStore();
  const [upgradeModule, setUpgradeModule] = useState<string | null>(null);

  const isAdmin = user?.perfil === "admin";

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
    <>
      <nav className="hidden md:block fixed top-0 left-0 right-0 z-50 bg-background border-b border-border">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center h-14 gap-1 overflow-x-auto">
            <Link href="/dashboard" className="text-accent font-bold text-lg mr-4 shrink-0">
              CF
            </Link>
            {navLinks.map((link) => {
              const restricted = isRestricted(link.href);

              if (restricted) {
                return (
                  <button
                    key={link.href}
                    onClick={() => setUpgradeModule(link.label)}
                    className="px-3 py-2 text-sm shrink-0 transition-colors text-muted/50 cursor-pointer flex items-center gap-1"
                  >
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
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
                  className={`px-3 py-2 text-sm shrink-0 transition-colors ${
                    isActive(link.href)
                      ? "text-accent border-b-2 border-accent"
                      : "text-foreground hover:text-accent"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
            {isAdmin && (
              <Link
                href="/admin/usuarios"
                className={`px-3 py-2 text-sm shrink-0 transition-colors ${
                  pathname.startsWith("/admin")
                    ? "text-accent border-b-2 border-accent"
                    : "text-foreground hover:text-accent"
                }`}
              >
                Admin
              </Link>
            )}
          </div>
        </div>
      </nav>

      <UpgradeModal
        isOpen={!!upgradeModule}
        onClose={() => setUpgradeModule(null)}
        moduleName={upgradeModule ?? ""}
      />
    </>
  );
}
