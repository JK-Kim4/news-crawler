const links = [
  { href: "/", label: "Feed" },
  { href: "/bookmarks", label: "Bookmarks" },
  { href: "/settings", label: "Alerts" },
  { href: "/admin", label: "Admin" },
  { href: "/login", label: "Login" },
];

export function TopNav() {
  return (
    <header className="sticky top-0 z-10 border-b border-ink/10 bg-sand/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div>
          <p className="font-display text-2xl text-ink">AI Insight Ledger</p>
          <p className="text-xs uppercase tracking-[0.3em] text-moss">Korean-first AI discovery desk</p>
        </div>
        <nav className="flex flex-wrap gap-3 text-sm text-ink/70">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="rounded-full border border-ink/10 px-4 py-2 transition hover:border-ember hover:text-ember"
            >
              {link.label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}

