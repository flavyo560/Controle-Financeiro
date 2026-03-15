"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";
import toast from "react-hot-toast";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { login } from "@/lib/auth";
import { useAuthStore } from "@/stores/authStore";
import type { Usuario } from "@/types";

const loginSchema = z.object({
  identificador: z.string().min(1, "Informe seu email, nome ou CPF"),
  senha: z.string().min(8, "A senha deve ter no mínimo 8 caracteres"),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [form, setForm] = useState<LoginForm>({ identificador: "", senha: "" });
  const [errors, setErrors] = useState<Partial<Record<keyof LoginForm, string>>>({});
  const [loading, setLoading] = useState(false);

  function handleChange(field: keyof LoginForm, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});

    const result = loginSchema.safeParse(form);
    if (!result.success) {
      const fieldErrors: Partial<Record<keyof LoginForm, string>> = {};
      result.error.errors.forEach((err) => {
        const field = err.path[0] as keyof LoginForm;
        fieldErrors[field] = err.message;
      });
      setErrors(fieldErrors);
      return;
    }

    setLoading(true);
    try {
      const { access_token, user } = await login(form.identificador, form.senha);
      setAuth(access_token, user as unknown as Usuario);
      toast.success("Login realizado com sucesso!");
      router.push("/dashboard");
    } catch {
      toast.error("Credenciais inválidas. Verifique seus dados e tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-accent mb-2">Controle Financeiro</h1>
          <p className="text-muted">Acesse sua conta para continuar</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-surface border border-border rounded-xl p-6 space-y-4"
        >
          <Input
            label="Email, nome ou CPF"
            placeholder="Digite seu email, nome ou CPF"
            value={form.identificador}
            onChange={(e) => handleChange("identificador", e.target.value)}
            error={errors.identificador}
            autoComplete="username"
          />

          <Input
            label="Senha"
            type="password"
            placeholder="Digite sua senha"
            value={form.senha}
            onChange={(e) => handleChange("senha", e.target.value)}
            error={errors.senha}
            autoComplete="current-password"
          />

          <Button
            type="submit"
            disabled={loading}
            className="w-full mt-2"
            size="lg"
          >
            {loading ? "Entrando..." : "Entrar"}
          </Button>

          <p className="text-center text-sm text-muted mt-4">
            Não tem uma conta?{" "}
            <a href="/cadastro" className="text-accent hover:underline">
              Cadastre-se
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
