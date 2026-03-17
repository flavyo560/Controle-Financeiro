"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const simpleLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/bancos", label: "Bancos" },
  { href: "/categorias", label: "Categorias" },
];

const lancamentosChildren = [
  { href: "/lancamentos/despesas", label: "Despesas" },
  { href: "/lancamentos/receitas", label: "Receitas" },
  { href: "/lancamentos/transferencias", label: "Transferências" },
];

const afterLinks = [
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
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  const linkClass = (href: string) =>
    `px-3 py-2 text-sm shrink-0 transition-colors ${
      isActive(href)
        ? "text-accent border-b-2 border-accent"
        : "text-foreground hover:text-accent"
    }`;

  return (
    <nav className="hidden md:block fixed top-0 left-0 right-0 z-50 bg-background border-b border-border">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center h-14 gap-1 overflow-x-auto">
          <Link href="/dashboard" className="text-accent font-bold text-lg mr-4 shrink-0">
            CF
          </Link>
          {simpleLinks.map((link) => (
            <Link key={link.href} href={link.href} className={linkClass(link.href)}>
              {link.label}
            </Link>
          ))}

          {/* Lançamentos dropdown */}
          <div
            className="relative"
            onMouseEnter={() => setDropdownOpen(true)}
            onMouseLeave={() => setDropdownOpen(false)}
          >
            <button
              className={`px-3 py-2 text-sm shrink-0 transition-colors ${
                isActive("/lancamentos")
                  ? "text-accent border-b-2 border-accent"
                  : "text-foreground hover:text-accent"
              }`}
            >
              Lançamentos ▾
            </button>
            {dropdownOpen && (
              <div className="absolute top-full left-0 mt-0 bg-surface border border-border rounded-lg shadow-lg py-1 min-w-[160px] z-50">
                {lancamentosChildren.map((child) => (
                  <Link
                    key={child.href}
                    href={child.href}
                    className={`block px-4 py-2 text-sm transition-colors ${
                      isActive(child.href)
                        ? "text-accent bg-accent/10"
                        : "text-foreground hover:bg-surface-hover hover:text-accent"
                    }`}
                  >
                    {child.label}
                  </Link>
                ))}
              </div>
            )}
          </div>

          {afterLinks.map((link) => (
            <Link key={link.href} href={link.href} className={linkClass(link.href)}>
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
