# """
# Cronjob: Quét DB tìm media status=PENDING rồi xử lý.
# Chạy: python cronjob_process_pending.py
# Hoặc dùng APScheduler để tự động lặp lại theo interval.
# """
#
# from __future__ import annotations
#
# import logging
# import time
# from datetime import datetime
#
# from apscheduler.schedulers.blocking import BlockingScheduler
# from sqlalchemy.orm import Session
#
# from api.deps import get_db
# from models.media_model import Media, Status
#
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
# )
# log = logging.getLogger(__name__)
#
#
# # ------------------------------------------------------------------ #
# #  Hàm xử lý từng media (thay phần TODO bằng logic thực của bạn)     #
# # ------------------------------------------------------------------ #
#
# def process_media(media: Media, db: Session) -> None:
#     """Xử lý 1 bản ghi media đang PENDING."""
#     log.info("⚙️  Đang xử lý media id=%s  file=%s", media.id, media.original_path)
#
#     try:
#         # ---------------------------------------------------------- #
#         # TODO: thêm logic thực tế vào đây, ví dụ:                   #
#         #   - Gọi FFmpeg để transcode / tạo thumbnail                 #
#         #   - Upload thumbnail lên MinIO                              #
#         #   - Cập nhật thumb_path                                     #
#         # ---------------------------------------------------------- #
#         time.sleep(20)
#
#         # Giả lập xử lý thành công → chuyển sang DONE
#         media.status = Status.COMPLETE.value
#         # media.thumb_path = "https://..."   # cập nhật nếu có
#
#         db.commit()
#         log.info("✅  media id=%s  → DONE", media.id)
#
#     except Exception as exc:
#         db.rollback()
#         # Chuyển sang FAILED để tránh bị quét lại vô tận
#         media.status = Status.FAIL.value
#         db.commit()
#         log.error("❌  media id=%s  thất bại: %s", media.id, exc)
#
#
# # ------------------------------------------------------------------ #
# #  Hàm chính: quét DB lấy tất cả PENDING rồi gọi process_media       #
# # ------------------------------------------------------------------ #
#
# def scan_and_process() -> None:
#     log.info("🔍  [%s] Bắt đầu quét PENDING...", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
#
#     db: Session = next(get_db())
#     try:
#         pending_list = (
#             db.query(Media)
#             .filter(Media.status == Status.PENDING.value)
#             .order_by(Media.created_at.asc())   # xử lý theo thứ tự upload
#             .all()
#         )
#
#         if not pending_list:
#             log.info("😴  Không có media nào cần xử lý.")
#             return
#
#         log.info("📋  Tìm thấy %d media PENDING.", len(pending_list))
#
#         for media in pending_list:
#             process_media(media, db)
#
#     finally:
#         db.close()
#
#     log.info("🏁  Hoàn thành lượt quét.")
#
#
# # ------------------------------------------------------------------ #
# #  Scheduler: chạy scan_and_process mỗi 30 giây                      #
# # ------------------------------------------------------------------ #
#
# if __name__ == "__main__":
#     # Chạy 1 lần ngay khi khởi động, sau đó lặp lại theo interval
#     scan_and_process()
#
#     scheduler = BlockingScheduler()
#     scheduler.add_job(
#         scan_and_process,
#         trigger="interval",
#         seconds=30,          # ← đổi thành 60 / 300 tuỳ nhu cầu
#         id="scan_pending",
#         max_instances=1,     # tránh 2 lượt chạy đè nhau
#     )
#
#     log.info("🚀  Scheduler khởi động, quét mỗi 30 giây. Ctrl+C để dừng.")
#     try:
#         scheduler.start()
#     except (KeyboardInterrupt, SystemExit):
#         log.info("🛑  Scheduler dừng.")