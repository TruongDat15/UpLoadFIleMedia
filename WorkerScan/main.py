
import logging
import sys
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = ROOT_DIR / "Server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from processer import process_media
from core.database import get_db
from logging_config import setup_logging
from models import Media, Status

setup_logging()
log = logging.getLogger(__name__)


def scan_and_process() -> None:
    log.info("🔍  [%s] Bắt đầu quét PENDING...", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    db: Session = next(get_db())
    try:
        pending_list = (
            db.query(Media)
            .filter(Media.status == Status.PENDING.value)
            .order_by(Media.created_at.asc())
            .all()
        )

        if not pending_list:
            log.info("😴  Không có media nào cần xử lý.")
            return

        log.info("📋  Tìm thấy %d media PENDING.", len(pending_list))

        for media in pending_list:
            process_media(media, db)

    finally:
        db.close()

    log.info("🏁  Hoàn thành lượt quét.")


# ------------------------------------------------------------------ #
#  Scheduler                                                          #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    scan_and_process()

    scheduler = BlockingScheduler()
    scheduler.add_job(
        scan_and_process,
        trigger="interval",
        seconds=30,
        id="scan_pending",
        max_instances=1,
    )

    log.info("🚀  Scheduler khởi động, quét mỗi 30 giây. Ctrl+C để dừng.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("🛑  Scheduler dừng.")
