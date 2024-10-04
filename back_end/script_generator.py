import os
import re
import json
import time
import requests
import resend
from crew import create_crew
from agents import news_researcher, senior_script_writer
from tasks import fetch_news_task, write_script_task

class ScriptGenerator:
    def __init__(self, progress_manager, job_id):

        self.progress_manager = progress_manager
        self.job_id = job_id
        self.Task_Completion_Counter = 0

        # Email
        resend.api_key = os.environ["RESEND_API_KEY"]
        self.params: resend.Emails.SendParams = {
            "from": "PAG <PAG@resend.dev>",
            "to": ["munnasai2000@gmail.com"],
            "subject": "OOPS!!",
            "html": "<strong>Change IT!!!!</strong>",
        }

    def task_callback(self, output):
        if self.Task_Completion_Counter == 0:
            self.progress_manager.update_progress(self.job_id, {
                "type": "string",
                "status": "News-Agent",
                "message": "News Researcher Agent has summarized the information from the top 3 websites.\n"
            })
            time.sleep(1)
            self.progress_manager.update_progress(self.job_id, {
                "type": "string",
                "status": "Writer-Agent",
                "message": "Script Writer Agent has started writing the script...\n"
            })
        elif self.Task_Completion_Counter == 1:
            self.progress_manager.update_progress(self.job_id, {
                "type": "string",
                "status": "Writer-Agent",
                "message": "Script Writer Agent has completed writing the output.\n"
            })

        # Increment the task counter
        self.Task_Completion_Counter += 1

    # Function to generate script using CrewAi
    def generate_script(self, topic):
        try:
            flag = True
            # Update the tasks with the correct inputs
            fetch_news_task.description = fetch_news_task.description.format(topic=topic)
            fetch_news_task.agent = news_researcher
            write_script_task.context = [fetch_news_task]
            write_script_task.agent = senior_script_writer

            # Create the crew
            crew = create_crew(
                agents=[news_researcher, senior_script_writer],
                tasks=[fetch_news_task, write_script_task],
                task_callback=self.task_callback
            )
            self.progress_manager.update_progress(self.job_id,{
                "type": "string",
                "status": "News-Agent",
                "message": 'News Researcher Agent Has Started Searching the Internet...'
            })
            script = crew.kickoff(inputs={'topic': topic})

            # Extract the JSON string from the raw result using regex
            json_str = re.search(r'\[.*\]', script, re.DOTALL).group()

            # Parse the JSON string into a list
            script_dict = json.loads(json_str)
            
            self.progress_manager.update_progress(self.job_id, {
                "type": "string",
                "status": "TTS",
                "message": "Audio Generation Has Started..\n",
                "no_of_dialogues":len(script_dict)
            })

            # Now process each line to convert text to speech
            for idx, line in enumerate(script_dict):

                if line.get('emotion') not in [
                    'female_happy', 'female_sad', 'female_angry', 'female_fearful', 
                    'female_disgust', 'female_surprised', 'male_happy', 'male_sad', 
                    'male_angry', 'male_fearful', 'male_disgust', 'male_surprised', None
                ]:
                    line['emotion'] = None
                    
                audio_url = self.text_to_speech_file(line)
                if audio_url:
                    # Send the audio URL to the progress manager
                    print("line_number : " ,idx, "text : " , line['text'] )
                    self.progress_manager.update_progress(self.job_id, {
                        "type": "audio",
                        "line_number": idx,
                        "audio_url": audio_url,
                        "text": line['text'],
                        "no_of_dialogues":len(script_dict)
                    })
                else:
                    # Handle the error by sending an error message
                    self.progress_manager.update_progress(self.job_id, {
                        "type": "error",
                        "status": "failed",
                        "message": f"Failed to generate audio for line {idx}."
                    })
                    
                    try:
                        email = resend.Emails.send(self.params)
                        print(email)
                    except Exception as e:
                        print(e)
                        
                    break


            self.progress_manager.update_progress(self.job_id, {
                "type": "string",
                "status": "TTS",
                "message": "Audio Generation Has Completed..\n",
                "no_of_dialogues":len(script_dict)
            })

            # Set the result in the progress manager
            self.progress_manager.set_result(self.job_id, script_dict)

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            self.progress_manager.set_error(self.job_id, error_message)

    def text_to_speech_file(self, line):
        # PlayHT API configuration
        url = "https://api.play.ht/api/v2/tts"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "AUTHORIZATION": os.environ["PLAYHT_API_KEY"],
            "X-USER-ID": os.environ["PLAYHT_USER_ID"]
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
        max_retries = 50  # Maximum number of times to poll
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
                output_data = status_data.get('output')
                audio_url = output_data.get("url")
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
