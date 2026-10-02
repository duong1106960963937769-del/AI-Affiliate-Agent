export const NO_DATA = "Chưa có dữ liệu";

export const money = (v: number | null | undefined, cur = "VND") =>
  v == null ? NO_DATA : `${Math.round(v).toLocaleString("vi-VN")} ${cur === "VND" ? "₫" : cur}`;
export const num = (v: number | null | undefined) => (v == null ? NO_DATA : v.toLocaleString("vi-VN"));
export const pct = (v: number | null | undefined, signed = false) =>
  v == null ? NO_DATA : `${signed && v > 0 ? "+" : ""}${v.toLocaleString("vi-VN", { maximumFractionDigits: 1 })}%`;
export const platformName = (p: string) => (p === "shopee" ? "Shopee" : "TikTok Shop");
export const competitionName = (c: string | null) =>
  c === "low" ? "Thấp" : c === "medium" ? "Trung bình" : c === "high" ? "Cao" : NO_DATA;
export const dateVN = (iso: string) => new Date(iso).toLocaleDateString("vi-VN");
