"use client";

import { useState, useRef } from "react";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import api from "@/lib/api";
import toast from "react-hot-toast";

export default function FerramentasPage() {
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleExport = async () => {
    setExporting(true);
    try {
      const { data } = await api.get("/ferramentas/backup/exportar", { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `backup_${new Date().toISOString().slice(0, 10)}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Backup exportado com sucesso");
    } catch {
      toast.error("Erro ao exportar backup");
    } finally {
      setExporting(false);
    }
  };

  const handleImport = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      toast.error("Selecione um arquivo JSON");
      return;
    }
    if (!file.name.endsWith(".json")) {
      toast.error("O arquivo deve ser .json");
      return;
    }

    setImporting(true);
    setErrors([]);
    try {
      const text = await file.text();
      const json = JSON.parse(text);
      await api.post("/ferramentas/backup/importar", json);
      toast.success("Backup importado com sucesso");
      if (fileRef.current) fileRef.current.value = "";
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string | string[] } } };
      if (axiosErr.response?.data?.detail) {
        const detail = axiosErr.response.data.detail;
        if (Array.isArray(detail)) {
          setErrors(detail);
        } else {
          setErrors([detail]);
        }
      } else {
        toast.error("Erro ao importar backup");
      }
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-xl font-semibold text-foreground">Ferramentas</h1>

      <Card title="Exportar Backup">
        <p className="text-sm text-muted mb-4">
          Exporte todos os seus dados em formato JSON. Você pode usar este arquivo para restaurar seus dados posteriormente.
        </p>
        <Button onClick={handleExport} disabled={exporting}>
          {exporting ? "Exportando..." : "Exportar Backup"}
        </Button>
      </Card>

      <Card title="Importar Backup">
        <p className="text-sm text-muted mb-4">
          Importe dados de um arquivo de backup JSON. Os dados existentes serão substituídos.
        </p>
        <div className="space-y-4">
          <input
            ref={fileRef}
            type="file"
            accept=".json"
            className="block w-full text-sm text-foreground file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-accent file:text-background hover:file:bg-accent-hover file:cursor-pointer"
          />
          <Button onClick={handleImport} disabled={importing} variant="secondary">
            {importing ? "Importando..." : "Importar Backup"}
          </Button>
        </div>
        {errors.length > 0 && (
          <div className="mt-4 p-3 rounded-lg bg-danger/10 border border-danger/20">
            <p className="text-sm font-medium text-danger mb-2">Erros na importação:</p>
            <ul className="list-disc list-inside text-sm text-danger space-y-1">
              {errors.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          </div>
        )}
      </Card>
    </div>
  );
}
