"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, ArrowUpRight, BriefcaseBusiness, ChevronRight, LayoutDashboard, Sparkles, Users } from "lucide-react";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/candidates", label: "Candidates", icon: Users },
  { href: "/jobs", label: "Jobs", icon: BriefcaseBusiness },
  { href: "/observability", label: "Observability", icon: Activity },
];

export function Nav() {
  const pathname = usePathname();
  const current = LINKS.find((link) => link.href === "/" ? pathname === "/" : pathname.startsWith(link.href));
  return (
    <>
      <aside className="workspace-sidebar">
        <Link href="/" className="brand" aria-label="AI Recruitment Copilot home">
          <span className="brand-mark"><Sparkles size={22} aria-hidden="true" /></span>
          <span>Recruitment<span className="brand-subtitle">AI COPILOT</span></span>
        </Link>
        <p className="nav-caption">WORKSPACE</p>
        <nav aria-label="Main navigation" className="workspace-nav">
          {LINKS.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link key={href} href={href} aria-current={active ? "page" : undefined} className={cn("nav-link", active && "nav-link-active")}>
                <Icon size={18} aria-hidden="true" /><span>{label}</span>
                {active && <ChevronRight size={15} className="nav-chevron" aria-hidden="true" />}
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-note">
          <Sparkles size={20} aria-hidden="true" />
          <p>A little intelligence.<br />A better match.</p>
          <span>From first CV to your next great hire.</span>
          <Link href="/jobs">Explore your roles <ArrowUpRight size={15} aria-hidden="true" /></Link>
        </div>
        <div className="sidebar-footer"><span className="workspace-avatar">RC</span><div>Recruiter workspace<span>AI Recruitment Copilot</span></div></div>
      </aside>
      <header className="workspace-topbar">
        <div className="flex items-center gap-2 text-sm"><span className="text-muted-foreground">Workspace</span><ChevronRight size={14} className="text-muted-foreground" aria-hidden="true" /><span className="font-medium">{current?.label ?? "Dashboard"}</span></div>
        <span className="topbar-label"><Sparkles size={14} aria-hidden="true" /> Recruitment, thoughtfully assisted</span>
      </header>
    </>
  );
}
