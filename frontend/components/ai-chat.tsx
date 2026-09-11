"use client";

import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

export function AIChat() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Ask about projects, customers, status, or other business data available to your role." },
  ]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function send(e: FormEvent) {
    e.preventDefault();
    const text = question.trim();
    if (!text || loading) return;

    setError("");
    setQuestion("");
    setMessages((current) => [...current, { role: "user", content: text }]);
    setLoading(true);

    try {
      const result = await api<{ answer: string }>("/ai/ask", {
        method: "POST",
        body: JSON.stringify({ message: text }),
      });
      setMessages((current) => [...current, { role: "assistant", content: result.answer }]);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card stack">
      <div>
        <h2>Ask My Business</h2>
        <p className="muted small">Database-grounded and filtered by your role.</p>
      </div>
      <div className="chat-window">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`chat-message ${message.role}`}>
            <strong>{message.role === "user" ? "You" : "Business AI"}</strong>
            <div style={{ whiteSpace: "pre-wrap" }}>{message.content}</div>
          </div>
        ))}
        {loading && <div className="chat-message assistant muted">Thinking…</div>}
      </div>
      <form className="stack" onSubmit={send}>
        <textarea
          className="input textarea chat-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Show me overdue projects"
          disabled={loading}
        />
        <button className="btn btn-lg" disabled={loading || !question.trim()}>
          {loading ? "Asking…" : "Ask Business"}
        </button>
      </form>
      {error && <div className="error">{error}</div>}
    </div>
  );
}
