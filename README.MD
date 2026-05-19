Hay đấy — đây là kiến trúc **async media processing pipeline** rất chuẩn, giống cách YouTube/Cloudinary hoạt động bên trong. Để làm mini project này tốt, bạn cần nắm vững một số lý thuyết nền trước.Trước tiên là sơ đồ toàn cảnh của hệ thống — hai process độc lập hoàn toàn, giao tiếp duy nhất qua DB.*(Nhấn vào từng ô để hỏi chi tiết hơn)*

---

Bây giờ là phần lý thuyết cốt lõi và kế hoạch code chi tiết:


## Lý thuyết cần nắm

**1. State machine cho media record**

Đây là trái tim của pipeline. Mỗi media record là một state machine với các trạng thái `pending → processing → ready` (hoặc `failed`). Lý do tách `processing` ra khỏi `pending` là để tránh race condition: nếu cronjob chạy 2 instance cùng lúc, cả hai sẽ không SELECT cùng 1 row đã bị UPDATE thành `processing`.

Pattern chuẩn là **SELECT FOR UPDATE SKIP LOCKED** (PostgreSQL) hoặc dùng optimistic locking. Với SQLite cho mini project, dùng transaction là đủ.

**2. Idempotency và at-least-once processing**

Cronjob phải được thiết kế để chạy lại an toàn. Nếu server crash giữa chừng khi đang process, record bị kẹt ở `processing`. Cần một cơ chế "stuck job recovery": nếu `processing` quá N phút, coi như bị stale và reset về `pending` để retry.

**3. ffmpeg là child process**

Từ Node.js/Python bạn spawn ffmpeg như một subprocess. Quan trọng: ffmpeg tốn CPU và RAM nặng — đây là lý do giới hạn `LIMIT 5` trong SELECT. Chạy song song quá nhiều sẽ OOM server.

**4. Backpressure**

Nếu upload nhiều hơn tốc độ xử lý, queue sẽ tích tụ. Mini project dùng `LIMIT 5` là đủ, nhưng production thực tế dùng message queue (Bull, RabbitMQ) thay cho cronjob polling DB.

---

## Kế hoạch mini project

Stack đề xuất: **Node.js + Express + SQLite + ffmpeg**. Gọn, không cần cài nhiều thứ.



Làm tuần tự để dễ debug:

1. Setup DB + schema
2. Server: 3 endpoints upload (init, chunk, complete) — test bằng `curl`
3. Verify file merge đúng (so MD5 với file gốc)
4. Cronjob: SELECT + UPDATE status — chạy thủ công trước
5. Tích hợp ffmpeg — test với file nhỏ trước
6. Thêm stuck-job recovery
7. Thêm simple status endpoint `GET /media/:id` để xem tiến trình

Bạn muốn mình viết code cho phần nào trước? Server upload hay cronjob worker?