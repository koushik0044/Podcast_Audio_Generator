import json
import logging
from pathlib import Path

import config
from agents import build_agents
from crew import create_crew
from schemas import PodcastScript
from tasks import build_tasks
from tts import build_tts

logger = logging.getLogger(__name__)

REFUSAL_MARKERS = ("i'm sorry", "i am sorry", "i can't provide", "i cannot provide")


def _is_refusal(script):
    """Safety-trained models sometimes decline the writing task and return the
    refusal *as* the script. Catch that so we never synthesize audio of a model
    apologizing, and fail with something actionable instead."""
    if len(script.lines) > 2:
        return False
    return any(
        marker in line.text.lower()
        for line in script.lines
        for marker in REFUSAL_MARKERS
    )


class ScriptGenerator:
    def __init__(self, progress_manager, job_id):
        self.progress_manager = progress_manager
        self.job_id = job_id
        self.topic = None
        self.tasks_completed = 0
        self.alert_sent = False
        self.tts = build_tts(on_quota_error=self._alert_quota_exhausted)

    def task_callback(self, _output):
        if self.tasks_completed == 0:
            self._progress(
                "News-Agent",
                "News Researcher Agent has summarized the information from the top 3 websites.\n",
            )
            self._progress(
                "Writer-Agent", "Script Writer Agent has started writing the script...\n"
            )
        elif self.tasks_completed == 1:
            self._progress(
                "Writer-Agent", "Script Writer Agent has completed writing the output.\n"
            )
        self.tasks_completed += 1

    def generate_script(self, topic):
        self.topic = topic
        try:
            news_researcher, senior_script_writer = build_agents()
            fetch_news_task, write_script_task = build_tasks(
                news_researcher, senior_script_writer
            )
            crew = create_crew(
                agents=[news_researcher, senior_script_writer],
                tasks=[fetch_news_task, write_script_task],
                task_callback=self.task_callback,
            )

            self._progress(
                "News-Agent", "News Researcher Agent Has Started Searching the Internet..."
            )
            # kickoff interpolates {topic} into the task descriptions itself.
            result = crew.kickoff(inputs={"topic": topic})
            script = self._parse_script(result)

            self._synthesize(script)
            self.progress_manager.set_result(
                self.job_id, [line.model_dump() for line in script.lines]
            )

        except Exception as exc:
            logger.exception("job %s failed", self.job_id)
            self.progress_manager.set_error(self.job_id, f"An error occurred: {exc}")

    def _synthesize(self, script):
        total = len(script.lines)
        self.progress_manager.update_progress(
            self.job_id,
            {
                "type": "string",
                "status": "TTS",
                "message": "Audio Generation Has Started..\n",
                "no_of_dialogues": total,
            },
        )

        job_dir = Path(config.AUDIO_ROOT) / self.job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        for idx, line in enumerate(script.lines):
            audio = self.tts.synthesize(line)
            (job_dir / f"{idx}.mp3").write_bytes(audio)
            logger.info("job %s line %s synthesized via %s", self.job_id, idx, self.tts.name)

            self.progress_manager.update_progress(
                self.job_id,
                {
                    "type": "audio",
                    "line_number": idx,
                    "audio_url": f"/audio/{self.job_id}/{idx}",
                    "text": line.text,
                    "no_of_dialogues": total,
                },
            )

        self.progress_manager.update_progress(
            self.job_id,
            {
                "type": "string",
                "status": "TTS",
                "message": "Audio Generation Has Completed..\n",
                "no_of_dialogues": total,
            },
        )

    @staticmethod
    def _parse_script(result):
        """CrewAI 1.x returns a CrewOutput. output_pydantic gives us a validated
        PodcastScript directly; fall back to the raw text only if that is absent."""
        if getattr(result, "pydantic", None):
            script = result.pydantic
        else:
            logger.warning("no structured output from the crew; parsing raw text")
            raw = result.raw if hasattr(result, "raw") else str(result)
            script = PodcastScript.model_validate(json.loads(raw))

        if _is_refusal(script):
            raise RuntimeError(
                "The writer model refused the task instead of producing a script. "
                "Try WRITER_MODEL=meta-llama/llama-4-scout-17b-16e-instruct."
            )
        return script

    def _progress(self, status, message):
        self.progress_manager.update_progress(
            self.job_id, {"type": "string", "status": status, "message": message}
        )

    def _alert_quota_exhausted(self, exc):
        """Fires once per job when ElevenLabs runs out of credits and we drop to
        the free voice. Optional: with no RESEND_API_KEY this just logs."""
        if self.alert_sent:
            return
        self.alert_sent = True

        if not (config.RESEND_API_KEY and config.ALERT_EMAIL_TO):
            logger.warning(
                "job %s degraded to the free voice (%s); email alert not configured",
                self.job_id,
                exc,
            )
            return

        try:
            import resend

            resend.api_key = config.RESEND_API_KEY
            resend.Emails.send(
                {
                    "from": config.ALERT_EMAIL_FROM,
                    "to": [config.ALERT_EMAIL_TO],
                    "subject": "Podcast Audio Generator: ElevenLabs unavailable",
                    "html": (
                        f"<p>Job <strong>{self.job_id}</strong> (topic: {self.topic}) "
                        f"fell back to the free voice.</p><p>{exc}</p>"
                    ),
                }
            )
            logger.info("sent quota alert for job %s", self.job_id)
        except Exception:
            logger.exception("failed to send quota alert for job %s", self.job_id)
