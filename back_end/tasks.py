from crewai import Task

from schemas import PodcastScript

# Tags the writer may use. Kept to a set eleven_v3 performs reliably.
AUDIO_TAGS = (
    "[laughs] [chuckles] [sighs] [gasps] [clears throat] "
    "[excited] [curious] [thoughtful] [calm] [nervous] [sarcastic] "
    "[whispers] [pauses] [hesitates]"
)


def build_tasks(news_researcher, senior_script_writer):
    """Fresh tasks per job.

    These used to be module-level singletons that the caller mutated in place --
    it formatted `{topic}` straight into the shared description, so every job
    after the first silently reran the *first* job's topic. Building them per job
    keeps the `{topic}` placeholder intact for Crew.kickoff(inputs=...) to
    interpolate, and stops concurrent jobs racing on shared state.
    """
    fetch_news_task = Task(
        description=(
            "Research the latest news on this topic: {topic}\n\n"
            "Call search_recent_news once with the topic as the search_query, then "
            "summarize what you find. Do not search repeatedly.\n"
            "Write a summary of at most 250 words covering the most newsworthy "
            "developments, including any specific facts, names, and dates."
        ),
        expected_output="A concise summary (max 250 words) of the recent news on the topic.",
        agent=news_researcher,
    )

    write_script_task = Task(
        description=(
            "Write an original podcast script about {topic}, informed by the News Researcher's summary. "
            "Two fictional hosts discuss the news in their own words: a male interviewer and a female "
            "interviewee, in a casual interview style. They are invented commentators, not real people, "
            "and they must not be presented as quoting anyone. Discuss the reported facts as commentary.\n\n"
            "Direct the vocal performance using audio tags, which are cues in square brackets placed inline "
            "in the spoken text. The voice model performs them. Use only these tags:\n"
            f"{AUDIO_TAGS}\n\n"
            "Guidance:\n"
            "- Place a tag immediately before the words it should colour, e.g. "
            '"[laughs] That is a great question."\n'
            "- Use tags sparingly, at most one or two per line. Unmarked lines are fine and sound natural.\n"
            "- Use an ellipsis (...) for a natural trailing pause.\n"
            "- Never write laughter phonetically (no \"hahaha\"); use [laughs].\n\n"
            "Produce 8 to 14 lines of dialogue. For each line set:\n"
            '- "text": the words to speak, with any audio tags inline.\n'
            '- "voice": "Male" for the interviewer, "Female" for the interviewee.\n'
            '- "stability": 0.0 to 1.0. Lower is more expressive and emotive, higher is more '
            "measured and consistent. Use around 0.3 for excited or emotional lines and around "
            "0.7 for calm, factual explanation. Default to 0.5.\n\n"
            # Single braces on purpose. CrewAI 1.x substitutes only {named} keys and
            # leaves other braces alone; it does NOT unescape {{ }}, so doubling them
            # would show the model malformed JSON.
            "Here is an example of two lines:\n"
            '{ "text": "[curious] So what actually changed this week?", "voice": "Male", "stability": 0.5 },\n'
            '{ "text": "[laughs] Everything, honestly... [pauses] let me start at the beginning.", "voice": "Female", "stability": 0.3 }'
        ),
        expected_output=(
            "A podcast script as a list of dialogue lines alternating between the male interviewer "
            "and the female interviewee, each with text (including inline audio tags), voice, and stability."
        ),
        agent=senior_script_writer,
        context=[fetch_news_task],
        output_pydantic=PodcastScript,
    )

    return fetch_news_task, write_script_task
