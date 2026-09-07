import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("itantra-theme");
    const isDark = stored === "dark";
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  const toggle = () => {
    setDark((prev) => {
      const next = !prev;
      document.documentElement.classList.toggle("dark", next);
      localStorage.setItem("itantra-theme", next ? "dark" : "light");
      return next;
    });
  };

  return (
    <button
      onClick={toggle}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      className="panel-surface inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-mono uppercase tracking-widest text-muted-foreground transition-colors hover:text-primary"
    >
      {dark ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
      {dark ? "Dark" : "Light"}
    </button>
  );
}
