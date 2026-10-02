import ProductExplorer from "@/components/ProductExplorer";
import { PageHeader } from "@/components/ui";

export default function Ranking() {
  return (
    <>
      <PageHeader title="Xếp hạng sản phẩm" desc="Bảng xếp hạng theo Product Opportunity Score (0–100). Điểm giảm khi thiếu dữ liệu; rê chuột vào điểm để xem độ tin cậy, mở sản phẩm để xem cách tính." />
      <ProductExplorer mode="ranking" />
    </>
  );
}
