export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api${path}`, { cache: "no-store", ...init });
  } catch {
    throw new ApiError("Không kết nối được máy chủ backend. Hãy chắc chắn backend đang chạy (xem hướng dẫn trong README).");
  }
  if (!res.ok) {
    let msg = `Lỗi ${res.status}`;
    try {
      const j = await res.json();
      msg = typeof j.detail === "string" ? j.detail : Array.isArray(j.detail) ? j.detail.map((d: { msg: string }) => d.msg).join("; ") : msg;
    } catch {}
    throw new ApiError(msg);
  }
  return res.json() as Promise<T>;
}

export type Product = {
  id: number; platform: "shopee" | "tiktok_shop"; name: string; url: string | null; image_url: string | null;
  category: string | null; price: number | null; currency: string; commission_rate: number | null;
  commission_per_order: number | null; rating: number | null; review_count: number | null;
  sold_count: number | null; growth_pct: number | null; competition: "low" | "medium" | "high" | null;
  video_fit: number | null; is_demo: boolean; source: string; source_label: string | null; is_favorite: boolean;
  data_updated_at: string; score: number | null; confidence: number; confidence_label: string;
};

export type Breakdown = { key: string; label: string; hint: string; weight: number; score: number | null; contribution: number | null; display: string };

export type ProductDetail = Product & {
  external_id: string; positive_review_pct: number | null; negative_review_pct: number | null;
  sold_30d: number | null; sold_prev_30d: number | null; return_rate: number | null;
  money: {
    nominal_commission_per_order: number | null; net_commission_estimate: number | null; product_revenue: number | null;
    estimated_profit: null; actual_profit: null; notes: Record<string, string>;
  };
  score_breakdown: Breakdown[]; score_raw_average: number | null; missing: string[]; explanation: string;
  pros: string[]; risks: string[]; video_tips: string[];
};

export type ListResponse = { total: number; page: number; page_size: number; items: Product[] };
export type Stats = { mode: "demo" | "real"; total: number; by_source: Record<string, number>; by_platform: Record<string, number>; favorites: number };

export function filtersToQuery(f: Record<string, string>): string {
  const p = new URLSearchParams();
  Object.entries(f).forEach(([k, v]) => v !== "" && v != null && p.set(k, v));
  return p.toString();
}
