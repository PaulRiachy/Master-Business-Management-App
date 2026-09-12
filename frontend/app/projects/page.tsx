"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

export default function Projects() {
  const [projects, setProjects] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [show, setShow] = useState(false);
  const [name, setName] = useState("");
  const [customer, setCustomer] = useState("");
  const [owner, setOwner] = useState("");
  const [due, setDue] = useState("");
  const [action, setAction] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [projectRows, customerRows, userRows] = await Promise.all([
        api<any[]>("/projects"),
        api<any[]>("/customers"),
        api<any[]>("/users"),
      ]);
      setProjects(projectRows);
      setCustomers(customerRows);
      setUsers(userRows);
      if (!customer && customerRows[0]) setCustomer(String(customerRows[0].id));
      if (!owner && userRows[0]) setOwner(String(userRows[0].id));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/projects", {
        method: "POST",
        body: JSON.stringify({
          project_name: name,
          customer_id: Number(customer),
          owner_id: Number(owner),
          due_date: due || null,
          next_action: action || null,
          financials: {},
        }),
      });
      setName("");
      setDue("");
      setAction("");
      setShow(false);
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <main className="container stack">
      <div className="row between">
        <div>
          <h1>Projects</h1>
          <p className="muted">Complete lifecycle from RFQ to Closed.</p>
        </div>
        <button className="btn btn-lg" onClick={() => setShow((value) => !value)}>
          {show ? "Close form" : "New RFQ"}
        </button>
      </div>

      {error && (
        <div className="card error-panel">
          <strong>Projects could not be loaded.</strong>
          <p>{error}</p>
          <p className="small muted">
            Make sure PostgreSQL and the FastAPI backend are running, then refresh the page.
          </p>
        </div>
      )}

      {show && (
        <form className="card grid two" onSubmit={create}>
          <label>
            Project name
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            Customer
            <select className="input" value={customer} onChange={(e) => setCustomer(e.target.value)}>
              {customers.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Owner
            <select className="input" value={owner} onChange={(e) => setOwner(e.target.value)}>
              {users.map((item) => <option key={item.id} value={item.id}>{item.name} ({item.role})</option>)}
            </select>
          </label>
          <label>
            Due date
            <input className="input" type="date" value={due} onChange={(e) => setDue(e.target.value)} />
          </label>
          <label style={{ gridColumn: "1 / -1" }}>
            Next action
            <input className="input" value={action} onChange={(e) => setAction(e.target.value)} placeholder="e.g. Confirm technical scope" />
          </label>
          <div><button className="btn">Create RFQ</button></div>
        </form>
      )}

      <div className="card table-card">
        {loading ? (
          <div className="loading">Loading projects…</div>
        ) : projects.length === 0 ? (
          <div className="loading"><strong>No projects yet.</strong><div className="small muted">Create an RFQ to start the workflow.</div></div>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Project</th><th>Customer</th><th>Status</th><th>Owner</th><th>Due</th><th>Margin</th></tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id}>
                  <td><Link className="link" href={`/projects/${project.id}`}>{project.project_name}</Link></td>
                  <td>{project.customer}</td>
                  <td><span className="badge">{project.status}</span></td>
                  <td>{project.owner}</td>
                  <td>{project.due_date || "—"}</td>
                  <td>{project.margin_percent != null ? `${Number(project.margin_percent).toFixed(1)}%` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}
