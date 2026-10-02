import type { ReactNode } from "react";
import { NO_DATA } from "@/lib/format";

export function Loading({ text = "Đang tải..." }: { text?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 p-8 text-slate-500">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600" />
      {text}
    </div>
  );
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <p className="font-medium">Đã xảy ra lỗi</p>
      <p className="mt-1">{message}</p>
      {onRetry && <button onClick={onRetry} className="mt-3 rounded-md bg-red-600 px-3 py-1.5 text-white hover:bg-red-700">Thử lại</button>}
    </div>
  );
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
      <p className="font-medium text-slate-700">{title}</p>
      <div className="mt-2 text-sm text-slate-500">{children}</div>
    </div>
  );
}

export function PageHeader({ title, desc, actions }: { title: string; desc?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        {desc && <p className="mt-1 max-w-3xl text-sm text-slate-500">{desc}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function DemoBadge() {
  return <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold tracking-wide text-amber-800" title="Dữ liệu hư cấu, không phải dữ liệu thị trường thật">DEMO</span>;
}

export function ScoreBadge({ score, confidence, label }: { score: number | null; confidence: number; label: string }) {
  if (score == null) return <span className="text-xs text-slate-400">{NO_DATA}</span>;
  const color = score >= 70 ? "bg-emerald-100 text-emerald-800" : score >= 50 ? "bg-sky-100 text-sky-800" : "bg-slate-100 text-slate-700";
  return (
    <span className="inline-flex flex-col items-start" title={`Độ tin cậy dữ liệu: ${label} (${Math.round(confidence * 100)}%)`}>
      <span className={`rounded-md px-2 py-0.5 text-sm font-semibold ${color}`}>{score.toFixed(1)}</span>
      <span className={`mt-0.5 text-[10px] ${confidence < 0.5 ? "text-orange-600" : "text-slate-400"}`}>tin cậy {label.toLowerCase()}</span>
    </span>
  );
}

export function PlatformTag({ platform }: { platform: string }) {
  const cls = platform === "shopee" ? "bg-orange-100 text-orange-800" : "bg-fuchsia-100 text-fuchsia-800";
  return <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${cls}`}>{platform === "shopee" ? "Shopee" : "TikTok Shop"}</span>;
}

export const btn = "rounded-lg px-3.5 py-2 text-sm font-medium transition disabled:opacity-50";
export const btnPrimary = `${btn} bg-indigo-600 text-white hover:bg-indigo-700`;
export const btnGhost = `${btn} border border-slate-300 bg-white text-slate-700 hover:bg-slate-50`;
export const inputCls = "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200";
