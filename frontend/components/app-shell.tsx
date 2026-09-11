"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";

export function AppShell({children}:{children:React.ReactNode}){
  const path = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const t = localStorage.getItem("mbm_token");
      const saved = JSON.parse(localStorage.getItem("mbm_user") || "null");
      if (t && saved) setUser(saved);
      else if (path !== "/login") router.replace("/login");
    } catch {
      if (path !== "/login") router.replace("/login");
    } finally {
      setReady(true);
    }
  }, [path, router]);

  const logout = () => {
    localStorage.removeItem("mbm_token");
    localStorage.removeItem("mbm_user");
    router.push("/login");
  };

  if (path === "/login") return <>{children}</>;
  if (!ready || !user) return <main className="auth"><div className="muted">Loading…</div></main>;

  const links = [
    ["Dashboard", "/dashboard"],
    ["Projects", "/projects"],
    ["Customers", "/customers"],
    ...(user.role !== "SALES" ? [["Suppliers", "/suppliers"]] : []),
  ];

  return <div className="shell">
    <header className="topbar">
      <div className="nav-wrap">
        <Link className="brand" href="/dashboard">Master Business</Link>
        <nav className="nav">
          {links.map(([label, href]) => <Link key={href} className={`nav-link ${path === href || path.startsWith(`${href}/`) ? "active" : ""}`} href={href}>{label}</Link>)}
        </nav>
      </div>
      <div className="user-bar">
        <span className="user-pill">{user.name} · {user.role}</span>
        <ThemeToggle />
        <button className="btn ghost nav-action" onClick={logout}>Log out</button>
      </div>
    </header>
    {children}
  </div>;
}
