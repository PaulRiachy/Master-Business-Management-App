const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export function token(){
  return typeof window !== "undefined" ? localStorage.getItem("mbm_token") : null;
}

export async function api<T>(path:string, options:RequestInit={}): Promise<T>{
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  const t = token();
  if (t) headers.set("Authorization", `Bearer ${t}`);

  let res: Response;
  try {
    res = await fetch(`${API}${path}`, { ...options, headers, cache: "no-store" });
  } catch {
    throw new Error(`Cannot reach the backend at ${API}. Make sure FastAPI is running on port 8000.`);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body?.detail || "Request failed";
    throw new Error(`${detail} (HTTP ${res.status})`);
  }

  return res.json() as Promise<T>;
}
