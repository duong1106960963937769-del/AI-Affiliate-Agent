"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ErrorBox, Loading, PageHeader } from "@/components/ui";

type Cost = {
  ai: { provider: string; model: string; label: string }; cloud: { label: string };
  marketplace_api: { marketplace: string; name: string; status: string; cost: string }[];
  estimated_monthly_usd: number | null; estimated_monthly_label: string; note: string;
};
type Usage = { service: string; requests_today: number; requests_month: number; errors: number; last_request: string | null; rate_limit: string; quota: string };

export default function System() {
  const [cost, setCost] = useState<Cost | null>(null);
  const [usage, setUsage] = useState<Usage[] | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    Promise.all([api<Cost>("/system/cost"), api<Usage[]>("/system/usage")]).then(([c, u]) => { setCost(c); setUsage(u); }).catch((e) => setErr(e.message));
  }, []);
  if (err) return <ErrorBox message={err} />;
  if (!cost || !usage) return <Loading />;
  return (
    <>
      <PageHeader title="Chi phí & API" desc="Hiển thị trung thực: chỉ ghi $0 khi thực sự không dùng dịch vụ trả phí nào; chưa biết giá thì ghi rõ." />
      <section className="mb-6 rounded-xl border bg-white p-5">
        <h2 className="mb-3 font-semibold">SYSTEM COST</h2>
        <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-[220px_1fr]">
          <dt className="text-slate-500">AI ({cost.ai.provider}, {cost.ai.model})</dt><dd className="font-medium">{cost.ai.label}</dd>
          {cost.marketplace_api.map((m) => (
            <><dt key={m.marketplace + "k"} className="text-slate-500">Marketplace API — {m.name}</dt><dd key={m.marketplace} className="font-medium">{m.cost}</dd></>
          ))}
          <dt className="text-slate-500">Cloud</dt><dd className="font-medium">{cost.cloud.label}</dd>
          <dt className="text-slate-500">Ước tính hàng tháng</dt><dd className="font-medium">{cost.estimated_monthly_label}</dd>
        </dl>
        <p className="mt-3 text-xs text-slate-400">{cost.note}</p>
      </section>
      <section className="rounded-xl border bg-white p-5">
        <h2 className="mb-3 font-semibold">API USAGE</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead className="text-left text-xs uppercase text-slate-500"><tr><th className="py-2">Dịch vụ</th><th>Hôm nay</th><th>Tháng này</th><th>Lỗi</th><th>Lần gọi cuối</th><th>Rate limit / Quota</th></tr></thead>
            <tbody>{usage.map((u) => (
              <tr key={u.service} className="border-t"><td className="py-2 font-medium">{u.service}</td><td>{u.requests_today}</td><td>{u.requests_month}</td><td>{u.errors}</td>
                <td>{u.last_request ? new Date(u.last_request).toLocaleString("vi-VN") : "Chưa có"}</td>
                <td className="text-xs text-slate-500">{u.rate_limit}<br />{u.quota}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </section>
    </>
  );
}
