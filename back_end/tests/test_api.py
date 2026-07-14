import pytest
from fastapi.testclient import TestClient

import config
import main


@pytest.fixture
def client(monkeypatch):
    # Never run the real crew/TTS pipeline from a test.
    monkeypatch.setattr(main, "run_script_generation", lambda topic, job_id: None)
    with TestClient(main.app) as c:
        yield c


def test_health(client):
    assert client.get("/health").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}


def test_generate_script_returns_a_job_id(client):
    response = client.post("/generate-script", json={"topic": "AI regulation"})
    assert response.status_code == 200

    job_id = response.json()["job_id"]
    assert main.progress_manager.get_progress(job_id) is not None


def test_generate_script_requires_a_topic(client):
    assert client.post("/generate-script", json={}).status_code == 422


def test_unknown_job_returns_404(client):
    # Previously this returned HTTP 200 with an {"error": ...} body.
    assert client.get("/progress/does-not-exist").status_code == 404


def test_progress_reports_a_known_job(client):
    job_id = client.post("/generate-script", json={"topic": "x"}).json()["job_id"]

    body = client.get(f"/progress/{job_id}").json()
    assert body["status"] == "started"
    assert body["progress"] == []


def test_audio_serves_a_generated_line(client, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "AUDIO_ROOT", str(tmp_path))
    job_dir = tmp_path / "job-1"
    job_dir.mkdir()
    (job_dir / "0.mp3").write_bytes(b"ID3fake-mp3-bytes")

    response = client.get("/audio/job-1/0")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"ID3fake-mp3-bytes"


def test_missing_audio_returns_404(client, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "AUDIO_ROOT", str(tmp_path))
    assert client.get("/audio/job-1/99").status_code == 404


def test_audio_path_cannot_escape_the_audio_root(client, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "AUDIO_ROOT", str(tmp_path / "audio"))
    (tmp_path / "audio").mkdir()
    (tmp_path / "secret.mp3").write_bytes(b"secret")

    assert client.get("/audio/..%2F/0").status_code == 404
