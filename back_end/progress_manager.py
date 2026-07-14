import logging
import shutil
import threading
import time
from pathlib import Path

import config

logger = logging.getLogger(__name__)


class ProgressManager:
    """In-memory job store, polled by the frontend via GET /progress/{job_id}.

    Single-process only: it does not survive a restart and breaks with
    uvicorn --workers > 1. Jobs are evicted by age and count so a long-lived
    server does not grow without bound, and each job's audio is deleted with it.
    """

    def __init__(self, ttl_seconds=None, max_jobs=None):
        self.jobs = {}
        self.lock = threading.Lock()
        self.ttl_seconds = ttl_seconds if ttl_seconds is not None else config.JOB_TTL_SECONDS
        self.max_jobs = max_jobs if max_jobs is not None else config.MAX_JOBS

    def create_job(self, job_id):
        with self.lock:
            self.jobs[job_id] = {
                "status": "started",
                "progress": [],
                "result": None,
                "error": None,
                "no_of_dialogues": None,
                "created_at": time.time(),
            }
            self._evict_locked()

    def update_progress(self, job_id, message):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]["progress"].append(message)

    def set_status(self, job_id, status):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = status

    def set_result(self, job_id, result):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]["result"] = result
                self.jobs[job_id]["status"] = "completed"

    def set_error(self, job_id, error_message):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]["error"] = error_message
                self.jobs[job_id]["type"] = "error"
                self.jobs[job_id]["status"] = "failed"

    def get_progress(self, job_id):
        with self.lock:
            return self.jobs.get(job_id)

    def _evict_locked(self):
        """Drop expired jobs, then oldest-first while over capacity.
        Caller must hold the lock."""
        cutoff = time.time() - self.ttl_seconds
        stale = [j for j, v in self.jobs.items() if v["created_at"] < cutoff]

        live = sorted(
            (j for j in self.jobs if j not in stale),
            key=lambda j: self.jobs[j]["created_at"],
        )
        overflow = live[: max(0, len(live) - self.max_jobs)]

        for job_id in stale + overflow:
            self.jobs.pop(job_id, None)
            self._delete_audio(job_id)

    @staticmethod
    def _delete_audio(job_id):
        job_dir = Path(config.AUDIO_ROOT) / job_id
        try:
            shutil.rmtree(job_dir)
        except FileNotFoundError:
            pass
        except OSError:
            logger.warning("could not remove audio dir for job %s", job_id, exc_info=True)
