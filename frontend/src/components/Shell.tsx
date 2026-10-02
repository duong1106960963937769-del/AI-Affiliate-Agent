"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const NAV = [
  { href: "/", label: "Dashboard", icon: "▦" },
  { href: "/discovery", label: "Tìm sản phẩm", icon: "🔍" },
  { href: "/ranking", label: "Xếp hạng", icon: "🏆" },
  { href: "/coming/creators", label: "Hồ sơ Creator", icon: "👤", soon: "P4" },
  { href: "/coming/scripts", label: "Script Studio", icon: "✍️", soon: "P3" },
  { href: "/coming/video", label: "Video Studio", icon: "🎬", soon: "P5" },
  { href: "/coming/library", label: "Thư viện video", icon: "🎞️", soon: "P5" },
  { href: "/coming/analytics", label: "Analytics", icon: "📈", soon: "P6" },
  { href: "/integrations", label: "Kết nối", icon: "🔌" },
  { href: "/system", label: "Chi phí & API", icon: "💲" },
  { href: "/settings", label: "Cài đặt", icon: "⚙️" },
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const [demo, setDemo] = useState(false);
  useEffect(() => {
    api<{ demo_mode: boolean }>("/settings/general").then((g) => setDemo(g.demo_mode)).catch(() => {});
  }, [path]);
  const nav = (
    <nav className="flex flex-col gap-1 p-3">
      {NAV.map((n) => {
        const active = n.href === "/" ? path === "/" : path.startsWith(n.href) || (n.href === "/ranking" && path.startsWith("/products"));
        return (
          <Link key={n.href} href={n.href} onClick={() => setOpen(false)}
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${active ? "bg-indigo-50 font-semibold text-indigo-700" : "text-slate-600 hover:bg-slate-100"}`}>
            <span className="w-5 text-center">{n.icon}</span>
            <span className="flex-1">{n.label}</span>
            {n.soon && <span className="rounded bg-slate-100 px-1.5 text-[10px] text-slate-500">{n.soon}</span>}
          </Link>
        );
      })}
    </nav>
  );
  return (
    <div className="min-h-screen md:flex">
      <header className="flex items-center justify-between border-b bg-white px-4 py-3 md:hidden">
        <span className="font-semibold text-indigo-700">AI Affiliate Agent</span>
        <button aria-label="Mở menu" onClick={() => setOpen(!open)} className="rounded border px-2 py-1">☰</button>
      </header>
      <aside className={`${open ? "block" : "hidden"} border-r bg-white md:block md:w-60 md:shrink-0`}>
        <div className="hidden px-5 py-5 text-lg font-bold text-indigo-700 md:block">AI Affiliate Agent</div>
        {nav}
        <p className="p-4 text-[11px] leading-snug text-slate-400">Foundation — chạy local, 0đ</p>
      </aside>
      <main className="min-w-0 flex-1 bg-slate-50 p-4 md:p-8">
        {demo && (
          <div role="status" className="mb-5 rounded-lg border border-amber-300 bg-amber-100 px-4 py-2 text-sm font-semibold text-amber-900">
            DEMO DATA — đang xem dữ liệu hư cấu, không phải dữ liệu thật. Tắt trong Cài đặt.
          </div>
        )}
        {children}
      </main>
    </div>
  );
}
