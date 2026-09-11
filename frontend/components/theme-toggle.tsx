"use client";
import { useEffect, useState } from "react";

export function ThemeToggle(){
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("mbm_theme");
    const initial = saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    setDark(initial);
    document.documentElement.dataset.theme = initial ? "dark" : "light";
  }, []);

  function toggle(){
    const next = !dark;
    setDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
    localStorage.setItem("mbm_theme", next ? "dark" : "light");
  }

  return <button className="icon-btn" type="button" onClick={toggle} aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}>
    {dark ? "☀ Light" : "☾ Dark"}
  </button>;
}
