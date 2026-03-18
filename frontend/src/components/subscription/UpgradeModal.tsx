"use client";

import { useRouter } from "next/navigation";
import Button from "@/components/ui/Button";

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  moduleName: string;
}

export default function UpgradeModal({ isOpen, onClose, moduleName }: UpgradeModalProps) {
  const router = useRouter();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-surface border border-border rounded-xl p-6 max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 mb-4">
          <span className="text-2xl">🔒</span>
          <h2 className="text-lg font-bold text-foreground">Módulo Exclusivo</h2>
        </div>

        <p className="text-sm text-muted mb-6">
          O módulo <span className="text-foreground font-medium">{moduleName}</span> está
          disponível apenas no <span className="text-accent font-semibold">Plano Plus</span>.
          Faça upgrade para acessar todas as funcionalidades.
        </p>

        <div className="flex gap-3">
          <Button variant="secondary" onClick={onClose} className="flex-1">
            Fechar
          </Button>
          <Button
            onClick={() => {
              onClose();
              router.push("/planos");
            }}
            className="flex-1"
          >
            Ver Planos
          </Button>
        </div>
      </div>
    </div>
  );
}
