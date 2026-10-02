import ProductExplorer from "@/components/ProductExplorer";
import { PageHeader } from "@/components/ui";

export default function Discovery() {
  return (
    <>
      <PageHeader title="Tìm sản phẩm" desc="Lọc sản phẩm từ dữ liệu bạn nhập (CSV) hoặc dữ liệu DEMO. Kết nối API trực tiếp với Shopee/TikTok Shop sẽ làm ở Phase 2 sau khi xác minh quyền truy cập." />
      <ProductExplorer mode="discovery" />
    </>
  );
}
