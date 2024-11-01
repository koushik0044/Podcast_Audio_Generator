import os
import uuid
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from progress_manager import ProgressManager
from script_generator import ScriptGenerator
import logging

logger = logging.getLogger(__name__)

# Define a Pydantic model for the expected input
class TopicRequest(BaseModel):
    topic: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create an instance of ProgressManager
progress_manager = ProgressManager()

@app.post("/generate-script")
async def create_script(request: TopicRequest, background_tasks: BackgroundTasks):
    # Generate a unique job ID
    job_id = str(uuid.uuid4())

    # Initialize the job in the progress manager
    progress_manager.create_job(job_id)

    # Start the script generation in the background
    background_tasks.add_task(run_script_generation, request.topic, job_id)

    # Return the job ID to the client
    return {"job_id": job_id}

def run_script_generation(topic, job_id):
    logger.info(f"Starting script generation for job_id: {job_id} with topic: {topic}")
    try:
        generator = ScriptGenerator(progress_manager, job_id)
        generator.generate_script(topic)
        logger.info(f"Completed script generation for job_id: {job_id}")
    except Exception as e:
        logger.error(f"Error in job {job_id}: {str(e)}")

@app.get("/progress/{job_id}")
async def get_progress(job_id: str):
    # Get the progress from the progress manager
    progress = progress_manager.get_progress(job_id)
    if progress is None:
        return {"error": "Invalid job ID"}
    else:
        return progress
