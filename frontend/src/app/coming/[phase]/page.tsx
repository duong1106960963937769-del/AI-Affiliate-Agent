"use client";
import { useParams } from "next/navigation";
import { Empty, PageHeader } from "@/components/ui";

const INFO: Record<string, { title: string; phase: string; text: string }> = {
  creators: { title: "Hồ sơ Creator", phase: "Phase 4", text: "Quản lý ảnh chân dung, xác nhận quyền sử dụng hình ảnh và xóa dữ liệu cá nhân." },
  scripts: { title: "Script Studio", phase: "Phase 3", text: "AI phân tích sản phẩm và tạo hook, kịch bản, shot list, prompt. Cần API key AI của bạn (có phí theo mức dùng)." },
  video: { title: "Video Studio", phase: "Phase 5", text: "Tạo video qua các provider sau khi xác minh API chính thức, quyền truy cập và chi phí. Sẽ luôn hỏi xác nhận trước khi phát sinh chi phí." },
  library: { title: "Thư viện video", phase: "Phase 5", text: "Quản lý, xem trước, duyệt hoặc yêu cầu sửa video đã tạo." },
  analytics: { title: "Analytics", phase: "Phase 6", text: "Nhập/đồng bộ lượt xem, đơn hàng, hoa hồng, chi phí để tính CTR, chuyển đổi và lợi nhuận." },
};

export default function Coming() {
  const { phase } = useParams<{ phase: string }>();
  const i = INFO[phase] ?? { title: "Tính năng", phase: "Sắp có", text: "" };
  return (
    <>
      <PageHeader title={i.title} />
      <Empty title={`Chưa phát triển — dự kiến ${i.phase}`}>{i.text}</Empty>
    </>
  );
}
