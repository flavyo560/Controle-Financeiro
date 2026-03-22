"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import axios from "axios";
import toast from "react-hot-toast";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function ResetarSenhaForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token") || "";

  const [senha, setSenha] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (senha.length < 4) {
      toast.error("A senha deve ter no mínimo 4 caracteres");
      return;
    }
    if (senha !== confirmar) {
      toast.error("As senhas não coincidem");
      return;
    }
    if (!token) {
      toast.error("Token inválido. Solicite um novo link.");
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API_URL}/auth/resetar-senha`, {
        token,
        nova_senha: senha,
      });
      toast.success("Senha redefinida com sucesso!");
      router.push("/login");
    } catch (err: unknown) {
      const msg =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : "Erro ao redefinir senha. O link pode ter expirado.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-md text-center">
          <h1 className="text-3xl font-bold text-accent mb-4">Link inválido</h1>
          <p className="text-muted mb-6">
            Este link de redefinição é inválido ou expirou.
          </p>
          <a href="/esqueci-senha">
            <Button className="w-full">Solicitar novo link</Button>
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-accent mb-2">Redefinir senha</h1>
          <p className="text-muted">Digite sua nova senha</p>
        </div>
        <form
          onSubmit={handleSubmit}
          className="bg-surface border border-border rounded-xl p-6 space-y-4"
        >
          <Input
            label="Nova senha"
            type="password"
            placeholder="Mínimo 4 caracteres"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            autoComplete="new-password"
          />
          <Input
            label="Confirmar senha"
            type="password"
            placeholder="Repita a nova senha"
            value={confirmar}
            onChange={(e) => setConfirmar(e.target.value)}
            autoComplete="new-password"
          />
          <Button type="submit" disabled={loading} className="w-full" size="lg">
            {loading ? "Redefinindo..." : "Redefinir senha"}
          </Button>
        </form>
      </div>
    </div>
  );
}

export default function ResetarSenhaPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><p className="text-muted">Carregando...</p></div>}>
      <ResetarSenhaForm />
    </Suspense>
  );
}
