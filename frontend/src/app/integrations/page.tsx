"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ErrorBox, Loading, PageHeader } from "@/components/ui";

type I = { key: string; name: string; platform: string; status: string; note: string };

export default function Integrations() {
  const [items, setItems] = useState<I[] | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => { api<I[]>("/integrations").then(setItems).catch((e) => setErr(e.message)); }, []);
  return (
    <>
      <PageHeader title="Kết nối" desc="Trạng thái các nguồn dữ liệu và dịch vụ. Chỉ kết nối nào hiển thị 'Sẵn sàng' mới thực sự hoạt động." />
      {err && <ErrorBox message={err} />}
      {!items && !err && <Loading />}
      <div className="grid gap-4 md:grid-cols-2">
        {items?.map((i) => (
          <div key={i.key} className="rounded-xl border bg-white p-4">
            <div className="flex items-center justify-between"><h2 className="font-semibold">{i.name}</h2>
              <span className={`rounded px-2 py-0.5 text-xs font-medium ${i.status === "available" ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>{i.status === "available" ? "Sẵn sàng" : "Chưa kết nối"}</span></div>
            <p className="mt-2 text-sm text-slate-600">{i.note}</p>
          </div>
        ))}
      </div>
      <p className="mt-6 text-xs text-slate-500">Không có kết nối nào lưu mật khẩu Shopee/TikTok. Khóa API (nếu có) sẽ đặt trong file .env trên máy bạn, không nằm trong mã nguồn.</p>
    </>
  );
}
