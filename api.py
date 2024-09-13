import os
import json
import re
import time
import requests
from pydantic import BaseModel
from fastapi import FastAPI
import threading
from queue import Queue, Empty
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool , ScrapeWebsiteTool
from langchain_groq import ChatGroq

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

# Define the ScriptGenerator class
class ScriptGenerator:
    def __init__(self, messages_queue):
        self.messages_queue = messages_queue
        self.Task_Completion_Counter = 0

    def task_callback(self, output):
        if self.Task_Completion_Counter == 0:
            self.messages_queue.put(json.dumps({"type": "status", "message": "News Researcher Agent has summarized the information from the top 3 websites.\n"}))
            time.sleep(1)
            self.messages_queue.put(json.dumps({"type": "status", "message": "Script Writer Agent has started writing the script...\n"}))
        elif self.Task_Completion_Counter == 1:
            self.messages_queue.put(json.dumps({"type": "status", "message": "Script Writer Agent has completed writing the output.\n"}))

        # Increment the task counter
        self.Task_Completion_Counter += 1

    # Function to generate script using CrewAi
    def generate_script(self , topic):

        llm = ChatGroq(api_key= os.environ['GROQ_API_KEY'] , model='llama-3.1-70b-versatile')
        google_search_tool = SerperDevTool(api_key=os.environ["SERPER_API_KEY"])

        # Agents
        news_researcher = Agent(
            role="News Researcher",
            goal="Summarize the information from the top three news articles for a given topic.",
            backstory=(
                "With years of experience in journalism, you have a keen eye for identifying newsworthy stories. "
                "Your expertise lies in quickly gathering and summarizing the most relevant and recent information from various sources. "
                "Your dedication to providing accurate and up-to-date news has earned you a reputation as a reliable and thorough researcher."
            ),
            llm=llm,
            tools=[google_search_tool , ScrapeWebsiteTool()],
            allow_delegation=False,
            verbose = False
        )

        senior_script_writer = Agent(
            role="Senior Script Writer",
            goal="Write a podcast script based on the provided news summary in the required format and within the specified constraints",
            llm=llm,
            allow_delegation=False,
            verbose = False,
            backstory=(
                "You are an experienced scriptwriter with a talent for creating engaging and informative content. "
                "You simplify complex topics and present them in an entertaining and easily digestible manner. "
                "You will write the script in the specified JSON format and within the specified constraints"
            )
        )

        # Tasks
        fetch_news_task = Task(
            description=(
                "Research and fetch the news articles summaries for the given topic. "
                "Ensure to get the recent and relevant articles. "
                "Use the search tool to get the latest news articles for the given topic and summarize the information. "
                "Topic: {topic}"
            ),
            expected_output='A summary of the news articles that are found on the topic.',
            agent=news_researcher,
            verbose = False,
            max_itrs=3,
        )

        write_script_task = Task(
            description = (
                "Generate a podcast script based on the information fetched from the news_researcher with two speakers: one male interviewer and one female interviewee."
                "The script should follow a casual interview style where one speaker interviews the other regarding the topic."
                'Use "....." for thoughtful pauses when the speaker is considering their response or the conversation shifts to a more serious tone. Use "hahahaha" to indicate laughter.'
                "The output should only contain the JSON object. Each JSON object should include:"
                ' 1) "text": "The text to be converted to speech.", "voice": "Male or Female",'
                ' 2) "emotion": The emotion of the dialogue . emotion must be one of [female_happy, female_sad, female_angry, female_fearful, female_disgust, female_surprised, male_happy, male_sad, male_angry, male_fearful, male_disgust, male_surprised, null] , '
                ' 3) "style_guidance": A Number between 12 to 17 . "Specify how strong the emotion should be using a number between 12 and 17. Use a lower value for less intense emotion and normal prosody, and a higher value to increase the emotion for more prosody.",'
                ' 4) "speed": A Number between 0.8 to 1 . "Control how fast the generated audio should be. A number between 0.8 and 1.0. Use slower speeds when the speaker is reflecting or the content is complex. Use faster speeds during lighter or more casual parts of the conversation." '
                "Absolutely make sure that the emotion is from the specified list"
                "Here's an example: "
                '{{ "text": "Why are you here?", "voice": "Male", "emotion": "male_angry", "style_guidance": 20, "speed": 1 }},'
                '{{ "text": "Well, thats a tough question..... Let me think about that for a moment.", "voice": "Female", "emotion": "female_fearful", "style_guidance": 10, "speed": 0.8 }} '
                "Start the script:"

            ),
            expected_output=(
                "A JSON-formatted podcast script. The script should contain a series of JSON objects representing the dialogue between the male interviewer and the female interviewee. \n"
                "The script should clearly reflect a casual interview style, with appropriate use of pauses (.....) and laughter (hahahaha) as indicated. \n"
                "Each JSON object must include the following fields: \n\n"
                '1) "text": The text that will be converted to speech. \n'
                '2) "voice": The gender of the speaker, either "Male" or "Female". \n'
                '3) "emotion": emotion must be one of female_happy, female_sad, female_angry, female_fearful, female_disgust, female_surprised, male_happy, male_sad, male_angry, male_fearful, male_disgust, male_surprised, null \n'
                '4) "style_guidance": A number between 12 and 17 indicating the intensity of the emotion, with higher values representing more intense emotions. \n'
                '5) "speed": A number between 0.8 and 1.0 representing the speed of the speech, with lower values for slower speeds and higher values for faster speeds. \n'
                "The output must ensure that all emotions are within the specified list."
            ),
            context = [fetch_news_task],
            agent=senior_script_writer,
            verbose = False,
            max_itrs=5
        )

        # crew
        crew = Crew(
            agents=[news_researcher, senior_script_writer ],
            tasks=[fetch_news_task, write_script_task ],
            verbose = False,
            task_callback = self.task_callback,
            process=Process.sequential,
        )

        script = crew.kickoff(inputs={'topic': topic})

        # Extract the JSON string from the raw result using regex
        json_str = re.search(r'\[.*\]', script, re.DOTALL).group()

        # Parse the JSON string into a dictionary
        script_dict = json.loads(json_str)

        # Now process each line to convert text to speech
        for idx, line in enumerate(script_dict):
            audio_url = self.text_to_speech_file(line)
            if audio_url:
                # Send the audio URL to the frontend
                self.messages_queue.put(json.dumps({
                    "type": "audio",
                    "line_number": idx,
                    "audio_url": audio_url
                }))
            else:
                # Handle the error by sending an error message
                self.messages_queue.put(json.dumps({
                    "type": "error",
                    "message": f"Failed to generate audio for line {idx}."
                }))

        return script_dict
    
    def text_to_speech_file(self, line):
        # PlayHT API configuration
        url = "https://api.play.ht/api/v2/tts"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "AUTHORIZATION": "915c31630817458e99c31711d833fb83",  # Replace with your actual PlayHT API key
            "X-USER-ID": "Qml8k8hUymTwQMC2lQjbefww76x1"       # Replace with your actual user ID
        }

        voice_link = (
            "s3://voice-cloning-zero-shot/4c627545-b9c0-4791-ae8e-f48f5475247c/bryansaad/manifest.json"
            if line["voice"] == "Male"
            else "s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/female-cs/manifest.json"
        )

        payload = {
            "text": line["text"],
            "voice": voice_link,
            "output_format": "mp3",
            "voice_engine": "PlayHT2.0",
            "speed": line["speed"],
            "quality": "high",
            "emotion": None if line["emotion"] == "null" else line["emotion"]
        }

        # Step 1: Submit the TTS request
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code not in (200, 201):
            error_message = f"Error encountered, status: {response.status_code}, content: {response.text}"
            print(error_message)
            return None

        # Step 2: Extract the job ID from the response
        response_data = response.json()
        job_id = response_data.get("id")
        if not job_id:
            print("Job ID not found in the response.")
            return None

        # Step 3: Poll the job status endpoint until the job is completed
        status_url = f"https://api.play.ht/api/v2/tts/{job_id}"
        max_retries = 10  # Maximum number of times to poll
        wait_time = 5     # Seconds between polls

        for attempt in range(max_retries):
            time.sleep(wait_time)
            status_response = requests.get(status_url, headers=headers)
            if status_response.status_code != 200:
                print(f"Failed to get job status, status: {status_response.status_code}, content: {status_response.text}")
                continue

            status_data = status_response.json()
            status = status_data.get("status")
            if status == "complete":
                # Step 4: Retrieve the audio URL
                audio_url = status_data.get("url")
                if audio_url:
                    return audio_url
                else:
                    print("Audio URL not found in the completed job response.")
                    return None
            elif status == "pending":
                print(f"Job {job_id} is still pending...")
                continue
            else:
                print(f"Job {job_id} failed with status: {status}")
                return None

        print(f"Job {job_id} did not complete within the expected time.")
        return None

@app.post("/generate-script")
async def create_script(request: TopicRequest):

    # Step 1: Generate script using CrewAi
    def event_generator():
        messages_queue = Queue()

        def run_generate_script():
            # Indicate the search has begun
            messages_queue.put(json.dumps({"type": "status", "message": "News Researcher Agent has started searching the internet...\n"}))
            try:
                # Create an instance of ScriptGenerator
                generator = ScriptGenerator(messages_queue)
                # Generate the script
                script = generator.generate_script(request.topic)
                time.sleep(1)
                # Indicate completion
                messages_queue.put(json.dumps({"type": "status", "message": "Completed script generation.\n"}))
                # Send the final script
                messages_queue.put(json.dumps({"type": "result", "script": script}))
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                messages_queue.put(json.dumps({"type": "error", "message": error_message}))

        # Start the generate_script function in a new thread
        thread = threading.Thread(target=run_generate_script)
        thread.start()

        # Continuously yield messages from the queue
        while thread.is_alive() or not messages_queue.empty():
            try:
                # Get the next message from the queue
                message = messages_queue.get(timeout=0.1)
                yield message + "\n"
            except Empty:
                continue

    return StreamingResponse(event_generator(), media_type="text/plain")
    
