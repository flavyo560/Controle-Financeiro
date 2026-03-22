"use client";

import Button from "@/components/ui/Button";

export default function EsqueciSenhaPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-accent mb-2">Esqueci minha senha</h1>
        </div>

        <div className="bg-surface border border-border rounded-xl p-6 space-y-4 text-center">
          <p className="text-foreground">
            Para resetar sua senha, entre em contato com o administrador do sistema.
          </p>
          <p className="text-muted text-sm">
            O administrador pode redefinir sua senha pelo painel de gestão de usuários.
          </p>
          <div className="pt-2">
            <a href="/login">
              <Button variant="secondary" className="w-full">Voltar ao Login</Button>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
