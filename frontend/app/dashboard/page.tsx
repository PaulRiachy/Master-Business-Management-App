"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AIChat } from "@/components/ai-chat";
import { api } from "@/lib/api";

type AttentionItem = {
  id: number;
  project_name: string;
  status: string;
  customer: string;
  owner: string;
  due_date?: string | null;
  next_action?: string | null;
  margin_percent?: number | null;
  hold?: boolean;
};

type Dashboard = {
  attention: AttentionItem[];
  active_rfqs: number;
  pending_quotes: number;
  active_orders: number;
  payments_due: number;
  shipment_holds: number;
};

export default function Dashboard() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [brief, setBrief] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Dashboard>("/dashboard")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  async function runBrief() {
    setLoading(true);
    setError("");
    try {
      const result = await api<{ brief: string }>("/ai/daily-brief", { method: "POST" });
      setBrief(result.brief);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (error && !data) {
    return (
      <main className="container stack">
        <div>
          <h1>Management Dashboard</h1>
          <p className="muted">The dashboard could not load.</p>
        </div>
        <div className="card error-panel">
          <strong>Could not load dashboard data</strong>
          <p>{error}</p>
          <p className="small muted">
            Check that the backend is running, then open <a href="http://localhost:8000/health" target="_blank" rel="noreferrer">/health</a>.
          </p>
        </div>
      </main>
    );
  }

  if (!data) {
    return <main className="container"><div className="card loading">Loading dashboard…</div></main>;
  }

  return (
    <main className="container stack">
      <div className="row between">
        <div>
          <h1>Management Dashboard</h1>
          <p className="muted">What needs attention right now.</p>
        </div>
        <button className="btn secondary btn-lg" onClick={runBrief} disabled={loading}>
          {loading ? "Generating…" : "Generate Daily Brief"}
        </button>
      </div>

      {error && <div className="card error-panel">{error}</div>}

      <section className="grid cards">
        <Stat label="Active RFQs" value={data.active_rfqs} />
        <Stat label="Pending Quotes" value={data.pending_quotes} />
        <Stat label="Active Orders" value={data.active_orders} />
        <Stat label="Payments Due" value={`$${Number(data.payments_due).toLocaleString()}`} />
      </section>

      <section className="grid two">
        <div className="card stack">
          <div className="row between">
            <h2>Needs My Attention</h2>
            {data.shipment_holds > 0 && <span className="badge red">{data.shipment_holds} shipment hold(s)</span>}
          </div>
          {data.attention.length === 0 ? (
            <p className="muted">Nothing urgent today.</p>
          ) : data.attention.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`} className="card attention" style={{ textDecoration: "none", color: "inherit" }}>
              <div className="row between">
                <strong>{p.project_name}</strong>
                <span className="badge">{p.status}</span>
              </div>
              <div className="small muted">{p.customer} · Owner: {p.owner}</div>
              <div className="small">
                {p.due_date && p.due_date < new Date().toISOString().slice(0, 10) ? <span className="badge red">Overdue</span> : null}{" "}
                {!p.next_action ? <span className="badge orange">Missing next action</span> : null}{" "}
                {p.margin_percent != null && p.margin_percent < 20 ? (
                  <span className="badge red">
                    Margin {Number(p.margin_percent).toFixed(1)}%
                  </span>
                ) : null}
                {p.hold ? <span className="badge red">Payment hold</span> : null}
              </div>
            </Link>
          ))}
        </div>

        <div className="stack">
          <AIChat />
          {brief && (
            <div className="card">
              <h2>Daily Brief</h2>
              <p style={{ whiteSpace: "pre-wrap" }}>{brief}</p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: any }) {
  return <div className="card"><div className="small muted">{label}</div><div className="big">{value}</div></div>;
}
