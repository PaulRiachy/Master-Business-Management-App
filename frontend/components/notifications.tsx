"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type AlertItem = {
  id: number;
  project_name: string;
  status: string;
  due_date?: string | null;
  next_action?: string | null;
  margin_percent?: number | null;
  hold?: boolean;
};

type Dashboard = { attention: AlertItem[] };

export function Notifications() {
  const [items, setItems] = useState<AlertItem[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api<Dashboard>("/dashboard")
      .then((data) => setItems(data.attention))
      .catch(() => setItems([]));
  }, []);

  return (
    <div className="notification-wrap">
      <button
        className="icon-btn notification-btn"
        aria-label={`Notifications${items.length ? `, ${items.length} alerts` : ""}`}
        onClick={() => setOpen((value) => !value)}
      >
        Alerts {items.length > 0 && <span className="notification-count">{items.length}</span>}
      </button>
      {open && (
        <div className="notification-panel card">
          <div className="row between">
            <strong>Needs attention</strong>
            {items.length > 0 && <span className="badge red">{items.length}</span>}
          </div>
          {items.length === 0 ? (
            <p className="small muted">Nothing urgent right now.</p>
          ) : (
            <div className="stack notification-list">
              {items.slice(0, 6).map((item) => (
                <Link key={item.id} href={`/projects/${item.id}`} className="notification-item" onClick={() => setOpen(false)}>
                  <strong>{item.project_name}</strong>
                  <span className="small muted">{item.status}</span>
                  {item.hold && <span className="badge red">Payment hold</span>}
                  {!item.next_action && <span className="badge orange">Missing next action</span>}
                  {item.due_date && item.due_date < new Date().toISOString().slice(0, 10) && <span className="badge red">Overdue</span>}
                  {item.margin_percent != null && item.margin_percent < 20 && <span className="badge red">Low margin</span>}
                </Link>
              ))}
            </div>
          )}
          {items.length > 6 && <p className="small muted">Open Dashboard to see all attention items.</p>}
        </div>
      )}
    </div>
  );
}
