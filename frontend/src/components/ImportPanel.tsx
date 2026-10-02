"use client";
import { useState } from "react";
import { API_URL } from "@/lib/api";
import { btnGhost, btnPrimary } from "./ui";

type Result = { created: number; updated: number; rejected: number; errors: { row: number; message: string }[] };

export default function ImportPanel({ onDone }: { onDone: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [res, setRes] = useState<Result | null>(null);

  async function submit() {
    if (!file) return;
    setBusy(true); setErr(""); setRes(null);
    try {
      const fd = new FormData(); fd.append("file", file);
      const r = await fetch(`${API_URL}/api/products/import`, { method: "POST", body: fd });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : `Lỗi ${r.status}`);
      setRes(j);
    } catch (e) {
      setErr(e instanceof TypeError ? "Không kết nối được backend." : (e as Error).message);
    } finally { setBusy(false); }
  }

  return (
    <div className="mb-5 rounded-xl border border-indigo-200 bg-indigo-50 p-4 text-sm">
      <p className="font-medium text-indigo-900">Nhập sản phẩm từ file CSV</p>
      <p className="mt-1 text-indigo-800">Cột bắt buộc: <code>platform</code> (shopee hoặc tiktok_shop) và <code>name</code>. Ô trống sẽ hiển thị &quot;Chưa có dữ liệu&quot; — hệ thống không tự điền số liệu. Dữ liệu chỉ lưu trên máy bạn.</p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <input type="file" accept=".csv,text/csv" onChange={(e) => { setFile(e.target.files?.[0] ?? null); setRes(null); }} />
        <button className={btnPrimary} disabled={!file || busy} onClick={submit}>{busy ? "Đang nhập..." : "Nhập dữ liệu"}</button>
        <a className={btnGhost} href={`${API_URL}/api/products/template.csv`}>Tải file mẫu</a>
      </div>
      {err && <p role="alert" className="mt-3 text-red-700">{err}</p>}
      {res && (
        <div className="mt-3 rounded-lg bg-white p-3">
          <p>Đã thêm <b>{res.created}</b>, cập nhật <b>{res.updated}</b>, từ chối <b className={res.rejected ? "text-red-700" : ""}>{res.rejected}</b> dòng.</p>
          {res.errors.length > 0 && (
            <ul className="mt-2 max-h-40 list-disc space-y-0.5 overflow-auto pl-5 text-red-700">
              {res.errors.map((e, i) => <li key={i}>Dòng {e.row}: {e.message}</li>)}
            </ul>
          )}
          <button className={btnPrimary + " mt-3"} onClick={onDone}>Xem danh sách</button>
        </div>
      )}
    </div>
  );
}
