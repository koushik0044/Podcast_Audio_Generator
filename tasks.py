from crewai import Task

# Tasks
fetch_news_task = Task(
    description=(
        "Research and fetch the news articles summaries for the given topic. "
        "Ensure to get the recent and relevant articles. "
        "Use the search tool to get the latest news articles for the given topic and summarize the information. "
        "Topic: {topic}"
    ),
    expected_output='A summary of the news articles that are found on the topic.',
    agent=None,
    verbose=False,
    max_itrs=3,
)

write_script_task = Task(
    description=(
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
        "A JSON-formatted podcast script. The script should contain a series of JSON objects representing the dialogue between the male interviewer and the female interviewee.\n"
        "The script should clearly reflect a casual interview style, with appropriate use of pauses (.....) and laughter (hahahaha) as indicated.\n"
        "Each JSON object must include the following fields:\n\n"
        '1) "text": The text that will be converted to speech.\n'
        '2) "voice": The gender of the speaker, either "Male" or "Female".\n'
        '3) "emotion": emotion must be one of [female_happy, female_sad, female_angry, female_fearful, female_disgust, female_surprised, male_happy, male_sad, male_angry, male_fearful, male_disgust, male_surprised, null]\n'
        '4) "style_guidance": A number between 12 and 17 indicating the intensity of the emotion, with higher values representing more intense emotions.\n'
        '5) "speed": A number between 0.8 and 1.0 representing the speed of the speech, with lower values for slower speeds and higher values for faster speeds.\n'
        "The output must ensure that all emotions are within the specified list."
    ),
    context=[],
    agent=None,
    verbose=False,
    max_itrs=5
)
