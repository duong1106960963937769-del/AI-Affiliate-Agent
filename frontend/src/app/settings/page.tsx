"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ErrorBox, Loading, PageHeader, btnGhost, btnPrimary, inputCls } from "@/components/ui";

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
      <PageHeader title="Cài đặt chấm điểm" desc="Điều chỉnh trọng số của từng tiêu chí trong Product Opportunity Score. Trọng số là mức quan trọng tương đối (hệ thống tự chuẩn hóa), đặt 0 để bỏ qua một tiêu chí." />
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
