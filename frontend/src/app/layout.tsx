import type { Metadata } from "next";
import "./globals.css";
import Shell from "@/components/Shell";

export const metadata: Metadata = {
  title: "AI Affiliate Agent",
  description: "Tìm, phân tích và xếp hạng sản phẩm affiliate",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="bg-slate-50 text-slate-900 antialiased">
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
