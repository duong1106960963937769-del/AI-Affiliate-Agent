"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, type ProductDetail } from "@/lib/api";
import { NO_DATA, competitionName, dateVN, money, num, pct } from "@/lib/format";
import { DemoBadge, ErrorBox, Loading, PageHeader, PlatformTag, btnGhost } from "@/components/ui";

function Row({ k, v, note }: { k: string; v: React.ReactNode; note?: string }) {
  return (
    <div className="flex justify-between gap-4 border-b py-2 text-sm last:border-0">
      <div><span className="text-slate-600">{k}</span>{note && <p className="text-[11px] text-slate-400">{note}</p>}</div>
      <span className={`text-right font-medium ${v === NO_DATA ? "!font-normal text-slate-400" : ""}`}>{v}</span>
    </div>
  );
}

export default function Detail() {
  const { id } = useParams<{ id: string }>();
  const [p, setP] = useState<ProductDetail | null>(null);
  const [err, setErr] = useState("");
  const load = useCallback(() => { api<ProductDetail>(`/products/${id}`).then(setP).catch((e) => setErr(e.message)); }, [id]);
  useEffect(load, [load]);

  if (err) return <><Link href="/ranking" className="text-sm text-indigo-600">← Quay lại</Link><div className="mt-3"><ErrorBox message={err} /></div></>;
  if (!p) return <Loading />;
  const m = p.money;

  return (
    <>
      <Link href="/ranking" className="text-sm text-indigo-600">← Quay lại bảng xếp hạng</Link>
      <div className="mt-3"><PageHeader title={p.name} desc={`Mã: ${p.external_id} · Nguồn: ${p.source_label ?? p.source} · Cập nhật ${dateVN(p.data_updated_at)}`}
        actions={<>
          <button className={btnGhost} onClick={async () => { await api(`/products/${p.id}/favorite?value=${!p.is_favorite}`, { method: "PUT" }); load(); }}>{p.is_favorite ? "★ Đã lưu yêu thích" : "☆ Lưu yêu thích"}</button>
          <button className={btnGhost} disabled title="Cần Phase 3–5 (Script Studio, Creator, Video provider)">🎬 Tạo video affiliate (sắp có)</button>
          {p.url && <a className={btnGhost} href={p.url} target="_blank" rel="noopener noreferrer">Mở trang sản phẩm ↗</a>}
        </>} /></div>
      <div className="mb-4 flex items-center gap-2"><PlatformTag platform={p.platform} />{p.is_demo && <DemoBadge />}{p.category && <span className="text-sm text-slate-500">{p.category}</span>}</div>
      {p.is_demo && <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">Sản phẩm DEMO hư cấu — mọi số liệu dưới đây không phải dữ liệu thật.</div>}

      <div className="grid gap-5 lg:grid-cols-3">
        <section className="rounded-xl border bg-white p-5 lg:col-span-1">
          <h2 className="mb-1 font-semibold">Opportunity Score</h2>
          <div className="mb-2 flex items-end gap-3"><span className="text-5xl font-bold text-indigo-700">{p.score == null ? "—" : p.score.toFixed(1)}</span><span className="pb-1 text-slate-400">/ 100</span></div>
          <p className="text-sm">Độ tin cậy dữ liệu: <b className={p.confidence < 0.5 ? "text-orange-600" : ""}>{p.confidence_label} ({Math.round(p.confidence * 100)}%)</b></p>
          <p className="mt-3 text-sm text-slate-600">{p.explanation}</p>
        </section>

        <section className="rounded-xl border bg-white p-5 lg:col-span-2">
          <h2 className="mb-3 font-semibold">Điểm từng tiêu chí</h2>
          <div className="space-y-3">
            {p.score_breakdown.map((b) => (
              <div key={b.key}>
                <div className="flex justify-between text-sm"><span>{b.label} <span className="text-xs text-slate-400">(trọng số {b.weight})</span></span><span className={b.score == null ? "text-slate-400" : "font-medium"}>{b.display}</span></div>
                <div className="mt-1 h-2 rounded bg-slate-100">{b.score != null && <div className="h-2 rounded bg-indigo-500" style={{ width: `${b.score}%` }} />}</div>
                <p className="mt-0.5 text-[11px] text-slate-400">{b.hint}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-xl border bg-white p-5">
          <h2 className="mb-2 font-semibold">Giá và hoa hồng</h2>
          <Row k="Giá bán" v={money(p.price, p.currency)} />
          <Row k="Tỷ lệ hoa hồng" v={pct(p.commission_rate)} />
          <Row k="Hoa hồng danh nghĩa / đơn" v={money(m.nominal_commission_per_order, p.currency)} note={m.notes.nominal} />
          <Row k="Hoa hồng thực nhận (ước tính)" v={money(m.net_commission_estimate, p.currency)} note={m.notes.net} />
          <Row k="Doanh thu của sản phẩm" v={money(m.product_revenue, p.currency)} note={m.notes.revenue} />
          <Row k="Lợi nhuận ước tính" v={NO_DATA} note={m.notes.profit} />
          <Row k="Lợi nhuận thực tế" v={NO_DATA} note="Chỉ có khi nhập đơn hàng và chi phí thật." />
        </section>

        <section className="rounded-xl border bg-white p-5">
          <h2 className="mb-2 font-semibold">Đánh giá và doanh số</h2>
          <Row k="Điểm đánh giá" v={p.rating == null ? NO_DATA : `${p.rating} ★`} />
          <Row k="Số lượng đánh giá" v={num(p.review_count)} />
          <Row k="Đánh giá tích cực" v={pct(p.positive_review_pct)} />
          <Row k="Đánh giá tiêu cực" v={pct(p.negative_review_pct)} />
          <Row k="Tổng đã bán" v={num(p.sold_count)} />
          <Row k="Bán 30 ngày gần nhất" v={num(p.sold_30d)} />
          <Row k="Bán 30 ngày trước đó" v={num(p.sold_prev_30d)} />
          <Row k="Tăng trưởng" v={pct(p.growth_pct, true)} note="Chỉ tính khi có cả hai kỳ dữ liệu." />
          <Row k="Tỷ lệ hoàn/hủy" v={pct(p.return_rate)} />
          <Row k="Mức độ cạnh tranh" v={competitionName(p.competition)} />
          <Row k="Phù hợp làm video (bạn chấm)" v={p.video_fit == null ? NO_DATA : `${p.video_fit}/5`} />
        </section>

        <section className="rounded-xl border bg-white p-5">
          <h2 className="mb-2 font-semibold">Ưu điểm và rủi ro</h2>
          <p className="text-xs text-slate-400">Chỉ suy ra từ số liệu có sẵn ở trên.</p>
          <h3 className="mt-3 text-sm font-medium text-emerald-700">Ưu điểm</h3>
          {p.pros.length ? <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">{p.pros.map((x) => <li key={x}>{x}</li>)}</ul> : <p className="text-sm text-slate-400">Chưa đủ dữ liệu để nêu ưu điểm.</p>}
          <h3 className="mt-3 text-sm font-medium text-red-700">Rủi ro</h3>
          {p.risks.length ? <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">{p.risks.map((x) => <li key={x}>{x}</li>)}</ul> : <p className="text-sm text-slate-400">Chưa phát hiện rủi ro từ dữ liệu hiện có.</p>}
        </section>

        <section className="rounded-xl border bg-white p-5 lg:col-span-3">
          <h2 className="mb-1 font-semibold">Gợi ý nội dung video (chung)</h2>
          <p className="mb-2 text-xs text-slate-400">Gợi ý theo dạng video, chưa phải kịch bản riêng cho sản phẩm. Script Studio dùng AI sẽ có ở Phase 3.</p>
          <ul className="list-disc space-y-1 pl-5 text-sm">{p.video_tips.map((x) => <li key={x}>{x}</li>)}</ul>
        </section>
      </div>
    </>
  );
}
