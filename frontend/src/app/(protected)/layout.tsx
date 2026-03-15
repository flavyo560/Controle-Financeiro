"use client";

import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Navbar />
      <Sidebar />
      <main className="pt-14 md:pt-16 px-4 pb-8 max-w-7xl mx-auto">
        {children}
      </main>
    </>
  );
}
