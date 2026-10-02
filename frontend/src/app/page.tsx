"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type ListResponse, type Stats } from "@/lib/api";

type Conn = { marketplace: string; name: string; status: string; status_label: string; last_sync_at: string | null };
import { DemoBadge, ErrorBox, Loading, PageHeader, PlatformTag, ScoreBadge, btnGhost, btnPrimary } from "@/components/ui";

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [top, setTop] = useState<ListResponse | null>(null);
  const [conns, setConns] = useState<Conn[]>([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const fetchAll = () => Promise.all([api<Stats>("/stats"), api<ListResponse>("/products?sort=score&page_size=5"), api<Conn[]>("/connections")]);
  const apply = ([s, t, c]: [Stats, ListResponse, Conn[]]) => { setStats(s); setTop(t); setConns(c); setErr(""); };
  const load = () => fetchAll().then(apply).catch((e) => setErr(e.message));
  useEffect(() => { fetchAll().then(apply).catch((e) => setErr(e.message)); }, []);

  async function run(fn: () => Promise<unknown>, confirmMsg?: string) {
    if (confirmMsg && !confirm(confirmMsg)) return;
    setBusy(true);
    try { await fn(); await load(); } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  const isDemo = stats?.mode === "demo";
  const real = stats && !isDemo ? stats.total : 0;

  return (
    <>
      <PageHeader title="Dashboard" desc="Tổng quan kết nối, dữ liệu sản phẩm và xếp hạng cơ hội." />
      {err && <ErrorBox message={err} onRetry={load} />}
      {!stats && !err && <Loading />}
      {stats && (
        <>
          <div className="grid gap-4 sm:grid-cols-2">
            {[[isDemo ? "Sản phẩm DEMO" : "Dữ liệu của bạn", stats.total], ["Yêu thích", stats.favorites]].map(([l, v]) => (
              <div key={l as string} className="rounded-xl border bg-white p-4">
                <p className="text-sm text-slate-500">{l}</p><p className="mt-1 text-3xl font-semibold">{v}</p>
              </div>
            ))}
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <section className="rounded-xl border bg-white p-4">
              <h2 className="mb-3 font-semibold">Kết nối sàn</h2>
              <ul className="space-y-2 text-sm">
                {conns.map((c) => (
                  <li key={c.marketplace} className="flex items-center justify-between gap-3">
                    <span>{c.name}</span>
                    <span className={c.status === "connected" ? "text-emerald-700" : c.status === "api_not_confirmed" ? "text-slate-500" : "text-amber-700"}>
                      {c.status === "connected" ? "✓ " : c.status === "not_linked" ? "○ " : "⚠ "}{c.status_label}
                    </span>
                  </li>
                ))}
              </ul>
              <Link href="/integrations" className="mt-3 inline-block text-sm text-indigo-600 underline">Chi tiết kết nối</Link>
            </section>
            <section className="rounded-xl border bg-white p-4">
              <h2 className="mb-3 font-semibold">Quét sản phẩm</h2>
              <div className="flex flex-wrap gap-2">
                {["SCAN TIKTOK", "SCAN SHOPEE", "SCAN BOTH"].map((l) => (
                  <button key={l} disabled title="Cần kết nối API chính thức được xác minh (Phase 2–3)" className={btnGhost}>{l}</button>
                ))}
              </div>
              <p className="mt-3 text-xs text-slate-500">Chưa khả dụng: API Shopee/TikTok Shop chưa được xác minh nên hệ thống không quét và không tạo dữ liệu giả. Hãy dùng <Link href="/discovery" className="text-indigo-600 underline">Nhập CSV</Link>.</p>
            </section>
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            <Link href="/discovery" className={btnPrimary}>Nhập CSV / Tìm sản phẩm</Link>
            <Link href="/ranking" className={btnGhost}>Xem xếp hạng</Link>
            {real > 0 && <button disabled={busy} className={btnGhost + " !text-red-700"} onClick={() => run(() => api("/data", { method: "DELETE" }), `Xóa vĩnh viễn ${real} sản phẩm bạn đã nhập? Không thể hoàn tác.`)}>Xóa dữ liệu của tôi</button>}
          </div>

          <h2 className="mb-3 mt-8 text-lg font-semibold">Top 5 theo Opportunity Score</h2>
          {top && top.items.length === 0 ? <p className="text-sm text-slate-500">Chưa có sản phẩm. Hãy nhập CSV, hoặc bật chế độ DEMO trong Cài đặt để xem thử.</p> : (
            <ul className="divide-y rounded-xl border bg-white">
              {top?.items.map((p) => (
                <li key={p.id} className="flex items-center justify-between gap-3 p-3">
                  <div className="min-w-0">
                    <Link href={`/products/${p.id}`} className="font-medium hover:text-indigo-600">{p.name}</Link>
                    <div className="mt-1 flex gap-1.5"><PlatformTag platform={p.platform} />{p.is_demo && <DemoBadge />}</div>
                  </div>
                  <ScoreBadge score={p.score} confidence={p.confidence} label={p.confidence_label} />
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </>
  );
}
