"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { useState } from "react";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "#141414",
            color: "#a4b0be",
            border: "1px solid #2d2d2d",
          },
          success: {
            iconTheme: { primary: "#00ffa3", secondary: "#0b0b0b" },
          },
          error: {
            iconTheme: { primary: "#ff4757", secondary: "#0b0b0b" },
          },
        }}
      />
    </QueryClientProvider>
  );
}
