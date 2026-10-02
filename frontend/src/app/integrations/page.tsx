"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ErrorBox, Loading, PageHeader, btnGhost } from "@/components/ui";

type C = {
  marketplace: string; name: string; status: string; status_label: string; availability: string; auth_method: string;
  is_free: string; requires_approval: string; note: string; doc_links: string[]; last_sync_at: string | null;
  can_connect: boolean; can_disconnect: boolean; can_refresh: boolean;
};

const tone = (s: string) => s === "connected" ? "bg-emerald-100 text-emerald-800" : s === "api_not_confirmed" ? "bg-slate-100 text-slate-600" : "bg-amber-100 text-amber-800";

export default function Integrations() {
  const [items, setItems] = useState<C[] | null>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState<Record<string, string>>({});

  const load = useCallback(() => api<C[]>("/connections").then((c) => { setItems(c); setErr(""); }).catch((e) => setErr(e.message)), []);
  useEffect(() => { load(); }, [load]);

  async function act(key: string, action: "connect" | "disconnect" | "refresh") {
    try { await api(`/connections/${key}/${action}`, { method: "POST" }); setMsg({ ...msg, [key]: "" }); await load(); }
    catch (e) { setMsg({ ...msg, [key]: (e as Error).message }); }
  }

  return (
    <>
      <PageHeader title="Kết nối sàn" desc="Chỉ kết nối nào hiển thị 'Đã kết nối' mới thực sự hoạt động. Ứng dụng không bao giờ hỏi hoặc lưu mật khẩu Shopee/TikTok; chỉ dùng cơ chế ủy quyền chính thức của sàn." />
      {err && <ErrorBox message={err} onRetry={load} />}
      {!items && !err && <Loading />}
      <div className="grid gap-4 md:grid-cols-2">
        {items?.map((c) => (
          <div key={c.marketplace} className="rounded-xl border bg-white p-4">
            <div className="flex items-center justify-between gap-2"><h2 className="font-semibold">{c.name}</h2>
              <span className={`rounded px-2 py-0.5 text-xs font-medium ${tone(c.status)}`}>{c.status === "connected" ? "✓ " : "⚠ "}{c.status_label}</span></div>
            <p className="mt-2 text-sm text-slate-600">{c.note}</p>
            <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-slate-500">
              <dt>Xác minh API</dt><dd className="font-medium text-slate-700">{c.availability}</dd>
              <dt>Cách xác thực</dt><dd className="font-medium text-slate-700">{c.auth_method}</dd>
              <dt>Miễn phí?</dt><dd className="font-medium text-slate-700">{c.is_free}</dd>
              <dt>Cần duyệt?</dt><dd className="font-medium text-slate-700">{c.requires_approval}</dd>
              <dt>Đồng bộ lần cuối</dt><dd className="font-medium text-slate-700">{c.last_sync_at ?? "Chưa có"}</dd>
            </dl>
            {c.doc_links.map((l) => <a key={l} href={l} target="_blank" rel="noopener noreferrer" className="mt-2 block truncate text-xs text-indigo-600 underline">Tài liệu chính thức: {l}</a>)}
            <div className="mt-3 flex flex-wrap gap-2">
              <button className={btnGhost} onClick={() => act(c.marketplace, "connect")}>Connect</button>
              {c.can_disconnect && <button className={btnGhost} onClick={() => act(c.marketplace, "disconnect")}>Disconnect</button>}
              {c.can_refresh && <button className={btnGhost} onClick={() => act(c.marketplace, "refresh")}>Refresh connection</button>}
            </div>
            {msg[c.marketplace] && <p role="alert" className="mt-3 rounded bg-amber-50 p-2 text-sm text-amber-900">{msg[c.marketplace]}</p>}
          </div>
        ))}
      </div>
      <p className="mt-6 text-xs text-slate-500">Nhập CSV vẫn hoạt động ở trang Tìm sản phẩm trong khi chờ API được xác minh.</p>
    </>
  );
}
