"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("mbm_token");
    router.replace(token ? "/dashboard" : "/login");
  }, [router]);

  return (
    <main className="auth">
      <div className="muted">Loading…</div>
    </main>
  );
}
