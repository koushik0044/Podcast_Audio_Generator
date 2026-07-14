import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import config
from progress_manager import ProgressManager
from script_generator import ScriptGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class TopicRequest(BaseModel):
    topic: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    missing = config.missing_required_keys()
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "See back_end/.env.example."
        )
    if not config.ELEVENLABS_API_KEY:
        logger.warning(
            "ELEVENLABS_API_KEY is not set - falling back to the free edge-tts voice."
        )
    yield


app = FastAPI(title="Podcast Audio Generator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    # Wildcard origins and credentials are mutually exclusive per the CORS spec,
    # and we use no cookies, so credentials stay off.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

progress_manager = ProgressManager()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate-script")
async def create_script(request: TopicRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    progress_manager.create_job(job_id)
    background_tasks.add_task(run_script_generation, request.topic, job_id)
    return {"job_id": job_id}


def run_script_generation(topic, job_id):
    logger.info("starting job %s for topic: %s", job_id, topic)
    try:
        ScriptGenerator(progress_manager, job_id).generate_script(topic)
        logger.info("completed job %s", job_id)
    except Exception:
        logger.exception("job %s failed", job_id)
        progress_manager.set_error(job_id, "Script generation failed.")


@app.get("/progress/{job_id}")
async def get_progress(job_id: str):
    progress = progress_manager.get_progress(job_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Invalid job ID")
    return progress


@app.get("/audio/{job_id}/{line_number}")
async def get_audio(job_id: str, line_number: int):
    """Audio used to be a PlayHT CDN URL. We synthesize bytes now, so we serve them."""
    # Resolve before comparing so ".." in job_id cannot escape the audio root.
    root = Path(config.AUDIO_ROOT).resolve()
    path = (root / job_id / f"{line_number}.mp3").resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(path, media_type="audio/mpeg")
