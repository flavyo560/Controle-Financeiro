"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/bancos", label: "Bancos" },
  { href: "/categorias", label: "Categorias" },
  { href: "/lancamentos/despesas", label: "Lançamentos" },
  { href: "/cartoes", label: "Cartões" },
  { href: "/investimentos", label: "Investimentos" },
  { href: "/frota", label: "Frota" },
  { href: "/orcamento", label: "Orçamento" },
  { href: "/relatorios/mensal", label: "Relatórios" },
  { href: "/ferramentas", label: "Ferramentas" },
  { href: "/perfil", label: "Perfil" },
];

export default function Navbar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  return (
    <nav className="hidden md:block fixed top-0 left-0 right-0 z-50 bg-background border-b border-border">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center h-14 gap-1 overflow-x-auto">
          <Link
            href="/dashboard"
            className="text-accent font-bold text-lg mr-4 shrink-0"
          >
            CF
          </Link>
          {navLinks.map((link) => (
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
          ))}
        </div>
      </div>
    </nav>
  );
}
