# AI Affiliate Agent

Ứng dụng tìm kiếm, phân tích và xếp hạng sản phẩm affiliate (Shopee, TikTok Shop), sau này mở rộng sang tạo kịch bản và video quảng cáo bằng AI.

**Trạng thái: Phase 1 (Foundation) — đã chạy được.** Chạy hoàn toàn trên máy bạn, chi phí 0đ, không gọi API trả phí nào. Xem mục "Chưa có gì" bên dưới để biết chính xác phần nào chưa hoạt động.

## Cần cài trước
- **Node.js 20+** (https://nodejs.org) và **Python 3.11+** (https://python.org). Không cần cài database: mặc định dùng SQLite.

## Lấy mã nguồn về máy
Cần cài [Git](https://git-scm.com/download/win) (hoặc tải ZIP từ GitHub). Phần mềm hiện nằm trên nhánh `claude/dazzling-goodall-5urr3c`:
```
git clone -b claude/dazzling-goodall-5urr3c https://github.com/duong1106960963937769-del/AI-Affiliate-Agent.git
cd AI-Affiliate-Agent
```

## Cách chạy

### Windows
Bấm đúp file `scripts\start.bat` (hoặc trong cmd, đã `cd` vào thư mục dự án: `scripts\start.bat`).
Lưu ý: gõ `scripts\start.bat` chứ **không** gõ `./scripts/start.sh` (lệnh đó chỉ dành cho Mac/Linux).
Lần đầu sẽ tự cài thư viện (vài phút), sau đó tự mở trình duyệt tại **http://localhost:3000**. Để dừng, đóng 2 cửa sổ đen.

### Mac / Linux
```bash
./scripts/start.sh
```
Mở **http://localhost:3000**, dừng bằng `Ctrl+C`.

### Chạy thủ công (2 terminal)
```bash
# Terminal 1 - backend
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8000

# Terminal 2 - giao diện
cd frontend && npm install && npm run dev
```
(Windows: dùng `python` thay `python3`, và `.venv\Scripts\uvicorn` thay `.venv/bin/uvicorn`.)

Tài liệu API tự động: http://localhost:8000/docs

## Cách dùng
1. **Cài đặt** → bật *Chế độ DEMO* để xem thử. Dữ liệu DEMO là **hư cấu**, nằm trong database riêng (`backend/data/demo.db`), luôn có thanh cảnh báo `DEMO DATA` và **không bao giờ trộn** với dữ liệu thật (đang bật DEMO thì không nhập CSV được).
2. **Tìm sản phẩm** → *Nhập CSV* (tải *file mẫu* để xem định dạng). Cột bắt buộc: `platform` (`shopee`/`tiktok_shop`) và `name`. Ô trống = "Chưa có dữ liệu", hệ thống không tự điền số. Dòng sai được báo rõ số dòng và lý do. Nhập lại file có cùng `external_id` sẽ cập nhật, không nhân đôi. Dùng bộ lọc rồi *Xuất CSV*.
3. **Xếp hạng** → sắp xếp theo điểm, hoa hồng/đơn, giá, đánh giá, số bán, tăng trưởng, phù hợp video.
4. Bấm vào sản phẩm → **trang chi tiết**: điểm từng tiêu chí, độ tin cậy, giải thích cách tính, ưu điểm/rủi ro, các khoản tiền tách bạch.
5. **Cài đặt** → chỉnh trọng số các tiêu chí; điểm tính lại ngay.

## Cách tính Opportunity Score (0–100)
9 tiêu chí (hoa hồng/đơn, đánh giá, số đánh giá, số bán, tăng trưởng, cạnh tranh, phù hợp video, % tích cực, rủi ro hoàn/hủy), mỗi tiêu chí 0–100 và có trọng số chỉnh được.
- Tiêu chí **thiếu dữ liệu bị bỏ khỏi phép tính** (không bị coi là 0, không bị bịa).
- **Độ tin cậy** = tổng trọng số tiêu chí có dữ liệu / tổng trọng số.
- **Điểm cuối = điểm trung bình × (0,6 + 0,4 × độ tin cậy)** → thiếu dữ liệu thì điểm thấp hơn.
- *Hoa hồng danh nghĩa* = giá × tỷ lệ; *thực nhận ước tính* chỉ tính khi có tỷ lệ hoàn/hủy thật; *doanh thu sản phẩm* ≠ thu nhập của bạn; *lợi nhuận* chưa tính ở Phase 1 (cần chi phí và đơn thật — Phase 6).
- Các mốc chuẩn hóa (vd. 10.000 đánh giá = 100 điểm) là quy ước của công thức, hiển thị ngay dưới từng tiêu chí; chỉ riêng mức hoa hồng mục tiêu chỉnh được trong Cài đặt.

## AI cục bộ (Ollama) — không bắt buộc ở Phase này
Ứng dụng chạy bình thường khi chưa có Ollama. Khi muốn dùng: cài từ https://ollama.com/download, mở cmd mới, chạy `ollama pull llama3.2:3b`, rồi vào **Cài đặt → Test AI Connection**. Chưa bật Ollama thì sẽ báo "Ollama is not running. Start Ollama and try again." Các AI trả phí (OpenAI/Gemini/Claude) cố ý **chưa được triển khai**.

## Kết nối sàn
Trang **Kết nối** hiển thị trạng thái thật. Hiện cả Shopee và TikTok Shop là `NOT CONFIRMED` (chưa xác minh được API chính thức), nên nút Connect từ chối rõ ràng và nút quét bị khóa; không có dữ liệu giả. Dùng *Nhập CSV* trong lúc chờ.

## Chi phí, API, logs
- **Chi phí & API**: chỉ ghi `$0` khi thực sự không dùng dịch vụ trả phí; giá chưa biết ghi `Pricing not confirmed`; quota không có thì ghi `Quota information unavailable`.
- **Logs** ở thư mục `logs/` (`app.log`, `api.log`, `scanner.log`, `error.log`), tự che `access_token`, `refresh_token`, `api_key`, `password`, `cookie`. Xem trong Cài đặt.
- Lỗi hiển thị thân thiện; chi tiết kỹ thuật chỉ ghi vào `logs/error.log`.
- Database dùng **Alembic**: tự nâng cấp khi khởi động, kể cả database của bản Phase 1 cũ (dữ liệu CSV của bạn được giữ nguyên; dữ liệu DEMO cũ lẫn trong database thật sẽ bị gỡ).

## Kiểm thử
```bash
cd backend && .venv/bin/python -m pytest -q      # test backend
cd frontend && npm run lint && npm run build     # kiểm tra giao diện
```

## Cấu trúc
- `backend/` FastAPI + SQLAlchemy (`app/services/scoring.py` công thức điểm, `csv_io.py` nhập/xuất CSV)
- `frontend/` Next.js + TypeScript + Tailwind
- `.env.example` mẫu cấu hình (không commit `.env`)

## Chưa có gì (chưa hoạt động)
- Kết nối API trực tiếp Shopee/TikTok Shop (Phase 2 — cần tài khoản affiliate được duyệt).
- Script Studio AI, Creator Profiles, Video Studio/Library, Quality Control, Analytics (Phase 3–6) — menu có trang "sắp có".
- Xếp hạng theo "phù hợp hồ sơ creator" (cần Phase 4).
- Quét sản phẩm (scan), OAuth, lưu token mã hóa (Phase 2–3; bảng dữ liệu đã sẵn sàng).
- Phân tích AI, review (cần Ollama; Phase 4). Creator Profile.
- Chưa có đăng nhập người dùng: chỉ chạy trên máy cá nhân (127.0.0.1), đừng mở ra Internet.

## Bảo mật & quyền riêng tư
Không lưu mật khẩu Shopee/TikTok; khóa API (nếu có sau này) chỉ ở `.env`. File upload bị giới hạn `.csv`, dung lượng và số dòng; CSV xuất có chống chèn công thức Excel. Dữ liệu chỉ lưu cục bộ trong `backend/data/`; có nút xóa dữ liệu của bạn trên Dashboard.
