"use client";

import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";
import TrialBanner from "@/components/subscription/TrialBanner";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
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
