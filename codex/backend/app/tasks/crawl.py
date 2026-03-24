from app.db.session import SessionLocal
from app.services.crawler import run_crawl


class EagerAsyncResult:
    def __init__(self, task_id: str):
        self.id = task_id


class ManualCrawlTask:
    def delay(self, source_ids: list[str], trigger: str = "manual") -> EagerAsyncResult:
        task_id = f"crawl-{trigger}-{len(source_ids)}"
        self(source_ids, trigger)
        return EagerAsyncResult(task_id)

    def __call__(self, source_ids: list[str], trigger: str = "manual") -> dict:
        db = SessionLocal()
        try:
            job = run_crawl(db, source_ids or None, trigger=trigger)
            return {"job_id": job.id, "status": job.status.value}
        finally:
            db.close()


trigger_manual_crawl = ManualCrawlTask()
