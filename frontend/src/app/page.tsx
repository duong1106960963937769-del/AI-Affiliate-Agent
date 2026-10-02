"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type ListResponse, type Stats } from "@/lib/api";
import { DemoBadge, ErrorBox, Loading, PageHeader, PlatformTag, ScoreBadge, btnGhost, btnPrimary } from "@/components/ui";

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [top, setTop] = useState<ListResponse | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const fetchAll = () => Promise.all([api<Stats>("/stats"), api<ListResponse>("/products?sort=score&page_size=5")]);
  const apply = ([s, t]: [Stats, ListResponse]) => { setStats(s); setTop(t); setErr(""); };
  const load = () => fetchAll().then(apply).catch((e) => setErr(e.message));
  useEffect(() => { fetchAll().then(apply).catch((e) => setErr(e.message)); }, []);

  async function run(fn: () => Promise<unknown>, confirmMsg?: string) {
    if (confirmMsg && !confirm(confirmMsg)) return;
    setBusy(true);
    try { await fn(); await load(); } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  const demo = stats?.by_source.demo ?? 0;
  const real = stats ? stats.total - demo : 0;

  return (
    <>
      <PageHeader title="Dashboard" desc="Tổng quan dữ liệu sản phẩm. Phase 1 tập trung vào phân tích và xếp hạng sản phẩm." />
      {err && <ErrorBox message={err} onRetry={load} />}
      {!stats && !err && <Loading />}
      {stats && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[["Tổng sản phẩm", stats.total], ["Dữ liệu của bạn (CSV)", real], ["Dữ liệu DEMO", demo], ["Yêu thích", stats.favorites]].map(([l, v]) => (
              <div key={l as string} className="rounded-xl border bg-white p-4">
                <p className="text-sm text-slate-500">{l}</p><p className="mt-1 text-3xl font-semibold">{v}</p>
              </div>
            ))}
          </div>

          {demo > 0 && (
            <div className="mt-5 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
              <b>Đang có dữ liệu DEMO.</b> Đây là sản phẩm hư cấu để trải nghiệm giao diện — <b>không phải dữ liệu thị trường thật</b>. Hãy xóa trước khi dùng để ra quyết định kinh doanh.
            </div>
          )}

          <div className="mt-5 flex flex-wrap gap-2">
            <Link href="/discovery" className={btnPrimary}>Nhập CSV / Tìm sản phẩm</Link>
            <Link href="/ranking" className={btnGhost}>Xem xếp hạng</Link>
            {demo === 0 && <button disabled={busy} className={btnGhost} onClick={() => run(() => api("/demo", { method: "POST" }))}>Nạp dữ liệu DEMO</button>}
            {demo > 0 && <button disabled={busy} className={btnGhost} onClick={() => run(() => api("/demo", { method: "DELETE" }), "Xóa toàn bộ dữ liệu DEMO?")}>Xóa dữ liệu DEMO</button>}
            {real > 0 && <button disabled={busy} className={btnGhost + " !text-red-700"} onClick={() => run(() => api("/data", { method: "DELETE" }), `Xóa vĩnh viễn ${real} sản phẩm bạn đã nhập? Không thể hoàn tác.`)}>Xóa dữ liệu của tôi</button>}
          </div>

          <h2 className="mb-3 mt-8 text-lg font-semibold">Top 5 theo Opportunity Score</h2>
          {top && top.items.length === 0 ? <p className="text-sm text-slate-500">Chưa có sản phẩm. Hãy nhập CSV hoặc nạp dữ liệu DEMO.</p> : (
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
