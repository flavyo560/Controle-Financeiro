"use client";

import { useState } from "react";
import axios from "axios";
import toast from "react-hot-toast";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function EsqueciSenhaPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [enviado, setEnviado] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) {
      toast.error("Informe seu email");
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API_URL}/auth/esqueci-senha`, { email });
      setEnviado(true);
      toast.success("Email enviado!");
    } catch {
      toast.error("Erro ao enviar. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  if (enviado) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-accent mb-2">Email enviado</h1>
          </div>
          <div className="bg-surface border border-border rounded-xl p-6 space-y-4 text-center">
            <p className="text-foreground">
              Se o email <span className="text-accent">{email}</span> estiver cadastrado,
              você receberá um link para redefinir sua senha.
            </p>
            <p className="text-muted text-sm">
              Verifique sua caixa de entrada e a pasta de spam.
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

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-accent mb-2">Esqueci minha senha</h1>
          <p className="text-muted">Informe seu email para receber o link de redefinição</p>
        </div>
        <form
          onSubmit={handleSubmit}
          className="bg-surface border border-border rounded-xl p-6 space-y-4"
        >
          <Input
            label="Email"
            type="email"
            placeholder="Digite seu email cadastrado"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
          <Button type="submit" disabled={loading} className="w-full" size="lg">
            {loading ? "Enviando..." : "Enviar link de redefinição"}
          </Button>
          <p className="text-center text-sm text-muted mt-4">
            <a href="/login" className="text-accent hover:underline">Voltar ao Login</a>
          </p>
        </form>
      </div>
    </div>
  );
}
