import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
};

const navItems = [
  { href: "/", label: "Home" },
  { href: "/register", label: "Register" },
  { href: "/login", label: "Login" },
  { href: "/artists", label: "Artists" },
  { href: "/tracks", label: "Tracks" },
  { href: "/review", label: "Review" },
];

export function AppShell({ children }: AppShellProps) {
  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-50">
      <header className="border-b border-zinc-800 bg-zinc-950/95">
        <nav className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-4 px-6 py-4">
          <a className="text-base font-semibold text-cyan-200" href="/">
            Sounds Right
          </a>
          <div className="flex flex-wrap gap-2">
            {navItems.map((item) => (
              <a
                className="rounded-md px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-900 hover:text-zinc-50"
                href={item.href}
                key={item.href}
              >
                {item.label}
              </a>
            ))}
          </div>
        </nav>
      </header>
      <div className="mx-auto w-full max-w-6xl px-6 py-8">{children}</div>
    </main>
  );
}
