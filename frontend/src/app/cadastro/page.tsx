"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { z } from "zod";
import toast from "react-hot-toast";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import api from "@/lib/api";

const cadastroSchema = z.object({
  nome: z.string().min(2, "O nome deve ter no mínimo 2 caracteres"),
  email: z.string().email("Informe um email válido"),
  senha: z.string().min(8, "A senha deve ter no mínimo 8 caracteres"),
  cpf: z.string().optional(),
  telefone: z.string().optional(),
});

type CadastroForm = z.infer<typeof cadastroSchema>;

const emptyForm: CadastroForm = {
  nome: "",
  email: "",
  senha: "",
  cpf: "",
  telefone: "",
};

export default function CadastroPage() {
  const router = useRouter();
  const [form, setForm] = useState<CadastroForm>(emptyForm);
  const [errors, setErrors] = useState<Partial<Record<keyof CadastroForm, string>>>({});
  const [loading, setLoading] = useState(false);

  function handleChange(field: keyof CadastroForm, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});

    const result = cadastroSchema.safeParse(form);
    if (!result.success) {
      const fieldErrors: Partial<Record<keyof CadastroForm, string>> = {};
      result.error.errors.forEach((err) => {
        const field = err.path[0] as keyof CadastroForm;
        fieldErrors[field] = err.message;
      });
      setErrors(fieldErrors);
      return;
    }

    setLoading(true);
    try {
      const payload = {
        nome: form.nome,
        email: form.email,
        senha: form.senha,
        cpf: form.cpf || null,
        telefone: form.telefone || null,
      };
      await api.post("/auth/register", payload);
      toast.success("Conta criada com sucesso! Faça login para continuar.");
      router.push("/login");
    } catch {
      toast.error("Erro ao criar conta. Verifique os dados e tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-accent mb-2">Criar Conta</h1>
          <p className="text-muted">Preencha os dados para se cadastrar</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-surface border border-border rounded-xl p-6 space-y-4"
        >
          <Input
            label="Nome"
            placeholder="Seu nome completo"
            value={form.nome}
            onChange={(e) => handleChange("nome", e.target.value)}
            error={errors.nome}
            autoComplete="name"
          />

          <Input
            label="Email"
            type="email"
            placeholder="seu@email.com"
            value={form.email}
            onChange={(e) => handleChange("email", e.target.value)}
            error={errors.email}
            autoComplete="email"
          />

          <Input
            label="Senha"
            type="password"
            placeholder="Mínimo 8 caracteres"
            value={form.senha}
            onChange={(e) => handleChange("senha", e.target.value)}
            error={errors.senha}
            autoComplete="new-password"
          />

          <Input
            label="CPF (opcional)"
            placeholder="000.000.000-00"
            value={form.cpf}
            onChange={(e) => handleChange("cpf", e.target.value)}
            error={errors.cpf}
          />

          <Input
            label="Telefone (opcional)"
            placeholder="(00) 00000-0000"
            value={form.telefone}
            onChange={(e) => handleChange("telefone", e.target.value)}
            error={errors.telefone}
          />

          <Button
            type="submit"
            disabled={loading}
            className="w-full mt-2"
            size="lg"
          >
            {loading ? "Cadastrando..." : "Cadastrar"}
          </Button>

          <p className="text-center text-sm text-muted mt-4">
            Já tem uma conta?{" "}
            <a href="/login" className="text-accent hover:underline">
              Faça login
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
