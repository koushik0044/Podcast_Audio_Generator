import time
from pathlib import Path

import config
from progress_manager import ProgressManager


def test_job_lifecycle():
    pm = ProgressManager()
    pm.create_job("job-1")
    assert pm.get_progress("job-1")["status"] == "started"

    pm.update_progress("job-1", {"type": "string", "message": "working"})
    pm.set_result("job-1", [{"text": "hi"}])

    job = pm.get_progress("job-1")
    assert job["status"] == "completed"
    assert job["result"] == [{"text": "hi"}]
    assert len(job["progress"]) == 1


def test_set_error_marks_job_failed():
    pm = ProgressManager()
    pm.create_job("job-1")
    pm.set_error("job-1", "boom")

    job = pm.get_progress("job-1")
    assert job["status"] == "failed"
    assert job["error"] == "boom"


def test_unknown_job_returns_none():
    assert ProgressManager().get_progress("nope") is None


def test_writes_to_unknown_job_are_ignored():
    pm = ProgressManager()
    pm.update_progress("ghost", {"message": "x"})
    pm.set_result("ghost", [])
    assert pm.get_progress("ghost") is None


def test_evicts_oldest_jobs_over_capacity():
    pm = ProgressManager(max_jobs=3)
    for i in range(5):
        pm.create_job(f"job-{i}")
        time.sleep(0.001)  # keep created_at ordering distinct

    assert pm.get_progress("job-0") is None
    assert pm.get_progress("job-1") is None
    assert pm.get_progress("job-4") is not None
    assert len(pm.jobs) == 3


def test_evicts_expired_jobs():
    pm = ProgressManager(ttl_seconds=0)
    pm.create_job("old")
    time.sleep(0.01)
    pm.create_job("new")

    assert pm.get_progress("old") is None


def test_eviction_deletes_the_jobs_audio(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "AUDIO_ROOT", str(tmp_path))
    audio_dir = tmp_path / "old"
    audio_dir.mkdir()
    (audio_dir / "0.mp3").write_bytes(b"fake mp3")

    pm = ProgressManager(ttl_seconds=0)
    pm.create_job("old")
    time.sleep(0.01)
    pm.create_job("new")

    assert not Path(audio_dir).exists()
