"use client";

import { useEffect } from "react";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";
import TrialBanner from "@/components/subscription/TrialBanner";
import { useAuthStore } from "@/stores/authStore";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const initialize = useAuthStore((s) => s.initialize);
  const isLoading = useAuthStore((s) => s.isLoading);

  useEffect(() => {
    initialize();
  }, [initialize]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted">Carregando...</p>
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <Sidebar />
      <div className="pt-14 md:pt-16">
        <TrialBanner />
        <main className="px-4 pb-8 max-w-7xl mx-auto mt-2">
          {children}
        </main>
      </div>
    </>
  );
}
