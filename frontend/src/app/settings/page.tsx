"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ErrorBox, Loading, PageHeader, btnGhost, btnPrimary, inputCls } from "@/components/ui";

type G = { ai_provider: string; ollama_model: string; max_products_per_scan: number; max_requests_per_scan: number; request_delay_seconds: number; retry_count: number; demo_mode: boolean };
type Storage = { database: string; database_path: string | null; database_bytes: number | null; logs_dir: string; log_files: string[]; uploads_dir: string };

function General() {
  const [g, setG] = useState<G | null>(null);
  const [st, setSt] = useState<Storage | null>(null);
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  const [ai, setAi] = useState<{ ok: boolean; message: string } | null>(null);
  const [testing, setTesting] = useState(false);
  const [log, setLog] = useState<{ name: string; lines: string[] } | null>(null);

  useEffect(() => {
    api<G>("/settings/general").then(setG).catch((e) => setErr(e.message));
    api<Storage>("/system/storage").then(setSt).catch(() => {});
  }, []);
  if (!g) return err ? <ErrorBox message={err} /> : <Loading />;
  const num = (k: keyof G) => (e: React.ChangeEvent<HTMLInputElement>) => setG({ ...g, [k]: Number(e.target.value) });

  async function save(patch: Partial<G>) {
    setErr(""); setMsg("");
    try { setG(await api<G>("/settings/general", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch) })); setMsg("Đã lưu."); }
    catch (e) { setErr((e as Error).message); }
  }
  async function test() {
    setTesting(true); setAi(null);
    try { setAi(await api("/ai/test", { method: "POST" })); } catch (e) { setAi({ ok: false, message: (e as Error).message }); } finally { setTesting(false); }
  }
  async function showLog(name: string) { setLog(await api(`/system/logs/${name}?lines=100`)); }

  return (
    <div className="mb-8 max-w-2xl space-y-5">
      <section className="rounded-xl border bg-white p-5">
        <h2 className="mb-1 font-semibold">AI Provider</h2>
        <p className="mb-3 text-xs text-slate-500">Chỉ dùng Ollama chạy trên máy bạn (miễn phí). Các dịch vụ AI trả phí chưa được triển khai.</p>
        <label className="text-sm font-medium">Nhà cung cấp
          <select className={inputCls + " mt-1"} value={g.ai_provider} onChange={(e) => setG({ ...g, ai_provider: e.target.value })}>
            <option value="ollama">Ollama (local)</option>
            <option disabled>OpenAI — chưa hỗ trợ (có phí)</option><option disabled>Gemini — chưa hỗ trợ (có phí)</option><option disabled>Claude — chưa hỗ trợ (có phí)</option>
          </select></label>
        <label className="mt-3 block text-sm font-medium">Model Ollama
          <input className={inputCls + " mt-1"} value={g.ollama_model} onChange={(e) => setG({ ...g, ollama_model: e.target.value })} /></label>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button className={btnPrimary} onClick={() => save({ ai_provider: g.ai_provider, ollama_model: g.ollama_model })}>Lưu</button>
          <button className={btnGhost} disabled={testing} onClick={test}>{testing ? "Đang kiểm tra..." : "Test AI Connection"}</button>
        </div>
        {ai && <p role="status" className={`mt-3 rounded p-2 text-sm ${ai.ok ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-900"}`}>{ai.ok ? "✓ " : "⚠ "}{ai.message}</p>}
      </section>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="mb-1 font-semibold">Giới hạn quét (scan)</h2>
        <p className="mb-3 text-xs text-slate-500">Mặc định thấp để tránh vượt giới hạn của sàn. Áp dụng khi tính năng quét được bật (Phase 3).</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm font-medium">Số sản phẩm tối đa mỗi lần quét<input type="number" min={1} max={500} className={inputCls + " mt-1"} value={g.max_products_per_scan} onChange={num("max_products_per_scan")} /></label>
          <label className="text-sm font-medium">Số request tối đa mỗi lần quét<input type="number" min={1} max={1000} className={inputCls + " mt-1"} value={g.max_requests_per_scan} onChange={num("max_requests_per_scan")} /></label>
          <label className="text-sm font-medium">Độ trễ giữa các request (giây)<input type="number" min={0.5} max={60} step={0.5} className={inputCls + " mt-1"} value={g.request_delay_seconds} onChange={num("request_delay_seconds")} /></label>
          <label className="text-sm font-medium">Số lần thử lại khi lỗi<input type="number" min={0} max={10} className={inputCls + " mt-1"} value={g.retry_count} onChange={num("retry_count")} /></label>
        </div>
        <button className={btnPrimary + " mt-3"} onClick={() => save({ max_products_per_scan: g.max_products_per_scan, max_requests_per_scan: g.max_requests_per_scan, request_delay_seconds: g.request_delay_seconds, retry_count: g.retry_count })}>Lưu giới hạn</button>
      </section>

      <section className="rounded-xl border bg-white p-5">
        <h2 className="mb-1 font-semibold">Chế độ DEMO</h2>
        <p className="mb-3 text-xs text-slate-500">Dùng dữ liệu hư cấu trong database riêng để thử giao diện. Không bao giờ trộn với dữ liệu thật; khi bật DEMO, việc nhập CSV bị khóa.</p>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={g.demo_mode} onChange={(e) => save({ demo_mode: e.target.checked }).then(() => window.location.reload())} /> Bật chế độ DEMO</label>
      </section>

      {st && (
        <section className="rounded-xl border bg-white p-5 text-sm">
          <h2 className="mb-2 font-semibold">Lưu trữ dữ liệu & Logs</h2>
          <p>Database: <b>{st.database}</b>{st.database_path && <> — <code className="break-all text-xs">{st.database_path}</code></>}{st.database_bytes != null && <> ({Math.round(st.database_bytes / 1024)} KB)</>}</p>
          <p className="mt-1">Thư mục log: <code className="break-all text-xs">{st.logs_dir}</code></p>
          <div className="mt-2 flex flex-wrap gap-2">{st.log_files.map((f) => <button key={f} className={btnGhost + " !py-1"} onClick={() => showLog(f.replace(".log", ""))}>{f}</button>)}</div>
          {log && <pre className="mt-3 max-h-64 overflow-auto rounded bg-slate-900 p-3 text-[11px] text-slate-100">{log.lines.length ? log.lines.join("\n") : "(log trống)"}</pre>}
          <p className="mt-2 text-xs text-slate-400">Log tự động che access_token, refresh_token, api_key, password, cookie.</p>
        </section>
      )}
      {err && <ErrorBox message={err} />}
      {msg && <p role="status" className="text-sm text-emerald-700">{msg}</p>}
    </div>
  );
}

type S = { weights: Record<string, number>; commission_target: number; criteria: { key: string; label: string; hint: string }[] };

export default function Settings() {
  const [s, setS] = useState<S | null>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => { api<S>("/settings").then(setS).catch((e) => setErr(e.message)); }, []);
  if (err && !s) return <ErrorBox message={err} />;
  if (!s) return <Loading />;
  const total = Object.values(s.weights).reduce((a, b) => a + b, 0);

  async function save() {
    setErr(""); setMsg("");
    try {
      const r = await api<S>("/settings", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ weights: s!.weights, commission_target: s!.commission_target }) });
      setS({ ...s!, ...r }); setMsg("Đã lưu. Điểm sản phẩm sẽ được tính lại theo cấu hình mới.");
    } catch (e) { setErr((e as Error).message); }
  }
  async function reset() {
    const r = await api<S>("/settings", { method: "DELETE" });
    setS({ ...s!, ...r }); setMsg("Đã khôi phục mặc định.");
  }

  return (
    <>
      <PageHeader title="Cài đặt" />
      <General />
      <h2 className="mb-3 text-lg font-semibold">Chấm điểm sản phẩm</h2>
      <p className="mb-4 max-w-2xl text-sm text-slate-500">Điều chỉnh trọng số của từng tiêu chí trong Product Opportunity Score. Trọng số là mức quan trọng tương đối (hệ thống tự chuẩn hóa), đặt 0 để bỏ qua một tiêu chí.</p>
      <div className="max-w-2xl rounded-xl border bg-white p-5">
        {s.criteria.map((c) => (
          <div key={c.key} className="mb-4">
            <div className="flex justify-between text-sm"><label htmlFor={c.key} className="font-medium">{c.label}</label><span>{s.weights[c.key]} ({total ? Math.round((s.weights[c.key] / total) * 100) : 0}%)</span></div>
            <input id={c.key} type="range" min={0} max={50} value={s.weights[c.key]} className="w-full" onChange={(e) => setS({ ...s, weights: { ...s.weights, [c.key]: Number(e.target.value) } })} />
            <p className="text-xs text-slate-400">{c.hint}</p>
          </div>
        ))}
        <div className="mb-4">
          <label htmlFor="ct" className="text-sm font-medium">Mức hoa hồng/đơn đạt 100 điểm (₫)</label>
          <input id="ct" type="number" min={1} className={inputCls + " mt-1 max-w-xs"} value={s.commission_target} onChange={(e) => setS({ ...s, commission_target: Number(e.target.value) })} />
          <p className="text-xs text-slate-400">Hoa hồng danh nghĩa/đơn bằng mức này hoặc cao hơn sẽ được 100 điểm tiêu chí &quot;Hoa hồng&quot;.</p>
        </div>
        {total <= 0 && <p className="mb-3 text-sm text-red-700">Tổng trọng số phải lớn hơn 0.</p>}
        {err && <div className="mb-3"><ErrorBox message={err} /></div>}
        {msg && <p role="status" className="mb-3 text-sm text-emerald-700">{msg}</p>}
        <div className="flex gap-2"><button className={btnPrimary} disabled={total <= 0 || !(s.commission_target > 0)} onClick={save}>Lưu cài đặt</button><button className={btnGhost} onClick={reset}>Khôi phục mặc định</button></div>
      </div>
      <p className="mt-6 max-w-2xl text-xs text-slate-500">Thiếu dữ liệu ở tiêu chí nào thì tiêu chí đó bị bỏ khỏi phép tính và độ tin cậy giảm; điểm cuối = điểm trung bình × (0,6 + 0,4 × độ tin cậy).</p>
    </>
  );
}
