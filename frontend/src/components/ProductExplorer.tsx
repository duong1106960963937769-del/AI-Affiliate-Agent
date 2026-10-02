"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { API_URL, api, filtersToQuery, type ListResponse } from "@/lib/api";
import { NO_DATA, competitionName, dateVN, money, num, pct } from "@/lib/format";
import { DemoBadge, Empty, ErrorBox, Loading, PlatformTag, ScoreBadge, btnGhost, inputCls } from "./ui";
import ImportPanel from "./ImportPanel";

const EMPTY = { q: "", platform: "", category: "", price_min: "", price_max: "", commission_min: "", rating_min: "",
  reviews_min: "", sold_min: "", competition: "", updated_within_days: "", source: "", favorites: "" };

const SORTS: [string, string][] = [["score", "Opportunity Score"], ["commission", "Hoa hồng/đơn"], ["price", "Giá bán"],
  ["rating", "Đánh giá"], ["sold", "Số lượng bán"], ["growth", "Tăng trưởng"], ["video_fit", "Phù hợp video"]];

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block text-xs font-medium text-slate-600">{label}<div className="mt-1">{children}</div></label>;
}

export default function ProductExplorer({ mode }: { mode: "discovery" | "ranking" }) {
  const [f, setF] = useState<Record<string, string>>(EMPTY);
  const [applied, setApplied] = useState<Record<string, string>>(EMPTY);
  const [sort, setSort] = useState("score");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<{ key: string; data?: ListResponse; err?: string } | null>(null);
  const [tick, setTick] = useState(0);
  const [cats, setCats] = useState<string[]>([]);
  const [showImport, setShowImport] = useState(false);
  const pageSize = mode === "ranking" ? 50 : 20;

  const query = filtersToQuery({ ...applied, sort, order, page: String(page), page_size: String(pageSize) });
  const key = `${query}|${tick}`;
  const load = () => setTick((t) => t + 1);

  useEffect(() => {
    let stale = false;
    api<ListResponse>(`/products?${query}`)
      .then((data) => !stale && setResult({ key, data }))
      .catch((e) => !stale && setResult({ key, err: e.message }));
    return () => { stale = true; };
  }, [query, key]);

  const loading = result?.key !== key;
  const data = result?.data ?? null;
  const err = loading ? "" : result?.err ?? "";
  useEffect(() => { api<{ categories: string[] }>("/products/meta").then((m) => setCats(m.categories)).catch(() => {}); }, [data?.total]);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value });
  const apply = (e?: React.FormEvent) => { e?.preventDefault(); setPage(1); setApplied(f); };
  const reset = () => { setF(EMPTY); setApplied(EMPTY); setPage(1); };
  const toggleFav = async (id: number, v: boolean) => { await api(`/products/${id}/favorite?value=${v}`, { method: "PUT" }); load(); };
  const exportUrl = `${API_URL}/api/products/export.csv?${filtersToQuery({ ...applied, sort, order })}`;
  const pages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;
  const hasFilter = Object.values(applied).some(Boolean);

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {mode === "discovery" && <button className="rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-indigo-700" onClick={() => setShowImport(!showImport)}>⬆ Nhập CSV</button>}
        <a className={btnGhost} href={exportUrl}>⬇ Xuất CSV (theo bộ lọc)</a>
      </div>
      {showImport && <ImportPanel onDone={() => { setShowImport(false); load(); }} />}

      <form onSubmit={apply} className="mb-5 rounded-xl border bg-white p-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Từ khóa"><input className={inputCls} value={f.q} onChange={set("q")} placeholder="Tên hoặc ngành hàng" /></Field>
          <Field label="Nền tảng">
            <select className={inputCls} value={f.platform} onChange={set("platform")}>
              <option value="">Tất cả</option><option value="shopee">Shopee</option><option value="tiktok_shop">TikTok Shop</option>
            </select>
          </Field>
          <Field label="Ngành hàng">
            <select className={inputCls} value={f.category} onChange={set("category")}>
              <option value="">Tất cả</option>{cats.map((c) => <option key={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Mức cạnh tranh">
            <select className={inputCls} value={f.competition} onChange={set("competition")}>
              <option value="">Tất cả</option><option value="low">Thấp</option><option value="medium">Trung bình</option><option value="high">Cao</option>
            </select>
          </Field>
          <Field label="Giá từ (₫)"><input type="number" min={0} className={inputCls} value={f.price_min} onChange={set("price_min")} /></Field>
          <Field label="Giá đến (₫)"><input type="number" min={0} className={inputCls} value={f.price_max} onChange={set("price_max")} /></Field>
          <Field label="Hoa hồng tối thiểu (%)"><input type="number" min={0} max={100} step="0.5" className={inputCls} value={f.commission_min} onChange={set("commission_min")} /></Field>
          <Field label="Điểm đánh giá tối thiểu (0–5)"><input type="number" min={0} max={5} step="0.1" className={inputCls} value={f.rating_min} onChange={set("rating_min")} /></Field>
          <Field label="Số đánh giá tối thiểu"><input type="number" min={0} className={inputCls} value={f.reviews_min} onChange={set("reviews_min")} /></Field>
          <Field label="Số lượng bán tối thiểu"><input type="number" min={0} className={inputCls} value={f.sold_min} onChange={set("sold_min")} /></Field>
          <Field label="Dữ liệu cập nhật trong">
            <select className={inputCls} value={f.updated_within_days} onChange={set("updated_within_days")}>
              <option value="">Mọi lúc</option><option value="1">1 ngày</option><option value="7">7 ngày</option><option value="30">30 ngày</option><option value="90">90 ngày</option>
            </select>
          </Field>
          <Field label="Nguồn dữ liệu">
            <select className={inputCls} value={f.source} onChange={set("source")}>
              <option value="">Tất cả</option><option value="demo">DEMO</option><option value="csv">CSV của tôi</option>
            </select>
          </Field>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">Áp dụng bộ lọc</button>
          <button type="button" className={btnGhost} onClick={reset}>Xóa bộ lọc</button>
          <label className="ml-2 flex items-center gap-2 text-sm text-slate-600">
            <input type="checkbox" checked={applied.favorites === "true"} onChange={(e) => { const v = { ...applied, favorites: e.target.checked ? "true" : "" }; setF(v); setApplied(v); setPage(1); }} /> Chỉ yêu thích
          </label>
        </div>
      </form>

      <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
        <span className="text-slate-500">Sắp xếp:</span>
        <select className="rounded-lg border border-slate-300 bg-white px-2 py-1.5" value={sort} onChange={(e) => { setSort(e.target.value); setPage(1); }}>
          {SORTS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </select>
        <button className={btnGhost + " !py-1.5"} onClick={() => setOrder(order === "desc" ? "asc" : "desc")}>{order === "desc" ? "Cao → thấp" : "Thấp → cao"}</button>
        <span className="text-xs text-slate-400">Sản phẩm thiếu dữ liệu của tiêu chí đang sắp xếp luôn nằm cuối. (Xếp hạng theo &quot;phù hợp hồ sơ creator&quot; sẽ có ở Phase 4.)</span>
        {data && <span className="ml-auto text-slate-500">{data.total} sản phẩm</span>}
      </div>

      {loading && <Loading />}
      {err && <ErrorBox message={err} onRetry={load} />}
      {!loading && !err && data && data.total === 0 && (
        hasFilter ? <Empty title="Không có sản phẩm khớp bộ lọc">Thử nới lỏng điều kiện lọc.</Empty>
          : <Empty title="Chưa có sản phẩm nào">Bấm <b>Nhập CSV</b> để nhập dữ liệu của bạn, hoặc bật chế độ DEMO ở trang <Link className="text-indigo-600 underline" href="/settings">Cài đặt</Link> để trải nghiệm.</Empty>
      )}
      {!loading && !err && data && data.total > 0 && (
        <div className="overflow-x-auto rounded-xl border bg-white">
          <table className="w-full min-w-[900px] text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="p-3">#</th><th className="p-3">Sản phẩm</th><th className="p-3 text-right">Giá</th>
                <th className="p-3 text-right">Hoa hồng</th><th className="p-3">Đánh giá</th><th className="p-3 text-right">Đã bán</th>
                <th className="p-3 text-right">Tăng trưởng</th><th className="p-3">Cạnh tranh</th><th className="p-3">Điểm</th><th className="p-3" />
              </tr>
            </thead>
            <tbody>
              {data.items.map((p, i) => (
                <tr key={p.id} className="border-t hover:bg-slate-50">
                  <td className="p-3 text-slate-400">{(page - 1) * pageSize + i + 1}</td>
                  <td className="max-w-xs p-3">
                    <Link href={`/products/${p.id}`} className="font-medium text-slate-900 hover:text-indigo-600">{p.name}</Link>
                    <div className="mt-1 flex flex-wrap items-center gap-1.5">
                      <PlatformTag platform={p.platform} />{p.is_demo && <DemoBadge />}
                      {p.category && <span className="text-xs text-slate-500">{p.category}</span>}
                    </div>
                    <div className="mt-0.5 text-[11px] text-slate-400">Cập nhật {dateVN(p.data_updated_at)}</div>
                  </td>
                  <td className="p-3 text-right">{money(p.price, p.currency)}</td>
                  <td className="p-3 text-right">
                    {p.commission_rate == null ? <span className="text-slate-400">{NO_DATA}</span> : <>{pct(p.commission_rate)}<div className="text-xs text-slate-500">≈ {money(p.commission_per_order, p.currency)}/đơn</div></>}
                  </td>
                  <td className="p-3">{p.rating == null ? <span className="text-slate-400">{NO_DATA}</span> : <>{p.rating}★<div className="text-xs text-slate-500">{num(p.review_count)} đánh giá</div></>}</td>
                  <td className="p-3 text-right">{num(p.sold_count)}</td>
                  <td className={`p-3 text-right ${p.growth_pct == null ? "text-slate-400" : p.growth_pct >= 0 ? "text-emerald-700" : "text-red-600"}`}>{pct(p.growth_pct, true)}</td>
                  <td className="p-3">{competitionName(p.competition)}</td>
                  <td className="p-3"><ScoreBadge score={p.score} confidence={p.confidence} label={p.confidence_label} /></td>
                  <td className="p-3"><button aria-label="Yêu thích" title="Yêu thích" onClick={() => toggleFav(p.id, !p.is_favorite)} className="text-lg">{p.is_favorite ? "★" : "☆"}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && pages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-3 text-sm">
          <button className={btnGhost} disabled={page <= 1} onClick={() => setPage(page - 1)}>← Trước</button>
          <span>Trang {page}/{pages}</span>
          <button className={btnGhost} disabled={page >= pages} onClick={() => setPage(page + 1)}>Sau →</button>
        </div>
      )}
    </div>
  );
}
