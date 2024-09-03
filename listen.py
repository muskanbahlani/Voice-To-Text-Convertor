import speech_recognition as sr
from database import save_recording, search_recording_by_date, search_recording_by_word, connect_to_db, setup_db, read_recording, last_n_recording, delete_recording 
from mail_service import send_email
from speak import text_to_speech
from datetime import datetime, timedelta
from summary_sumy import generate_summary
from keywords import top_frequent_words
import config
import time

flag = 1  # Global flag to control the recording loop
sum_text = ""  # Variable to store the summarized text

def stop():
    """Function to stop the recording process."""
    config.recording_state = 0
    return

def command_process(command_text, text, start_time):
    """Process voice commands to control recording and perform actions."""
    command1 = "start recording"
    command2 = "stop recording"
    command3 = "send text to mail"
    command4 = "search database for"

    # Check for any command in the recognized text
    if command1 in command_text.lower():
        print("Recording started...")
        text_to_speech("Recording started...")
        return "start"
    elif command2 in command_text.lower():
        print("Recording stopped")
        text_to_speech("Recording stopped")
        sum_text = generate_summary(text)
        save_recording(text, sum_text, start_time)
        return "stop"
    elif command3 in command_text.lower():
        print("Recording stopped")
        text_to_speech("Recording stopped")
        sum_text = generate_summary(text)
        save_recording(text, sum_text, start_time)
        # Uncomment the following line to send the email
        # send_email(text)
        return "stop"
    elif command4 in command_text.lower():
        # Extract search query from the command
        search_query = command_text.split("search database for", 1)[1].strip()
        search_recording_by_word(search_query)
        print("Recording stopped")
        text_to_speech("Recording stopped")
        return "stop"

def new_listen_updates():
    """Main function to listen to and process voice commands and text."""
    r = sr.Recognizer()
    text = ""
    with sr.Microphone() as source:
        print("Recording started...")
        text_to_speech("Recording started...")
        yield "Recording started..."
        
        start_time = datetime.now()  # Capture the start time of recording
        print(f'The start time for the listening is: {start_time}\n')
        time_limit = timedelta(seconds=200)  # Set a time limit for recording

        config.recording_state = 1  # Set the recording state to active
        
        while True:
            if config.recording_state == 0:  # Check if the recording should stop
                break
            print(f"The duration of recording is: {datetime.now() - start_time} and limit: {time_limit}")
            if datetime.now() - start_time >= time_limit:
                yield f"Recording stopped because the time limit of {time_limit} seconds has been passed.\n"
                break

            # Listen to the audio input
            audio = r.listen(source, phrase_time_limit=20)
            try:
                recorded_text = r.recognize_google(audio)  # Convert audio to text
                print("The recorded text is: ", recorded_text)
                text += " " + recorded_text
                yield recorded_text
            except sr.UnknownValueError:
                yield "Could not understand audio"
            except sr.RequestError as e:
                yield f"Error: {e}"

            if config.recording_state == 0:  # Stop recording if instructed
                break

        yield "Recording stopped!!!"
        text_to_speech("Recording stopped")
        final_text = "The recorded text is: " + text
        yield final_text
        time.sleep(1)
        yield "Working on the summary..."
        text_to_speech("Working on the summary...")
        
        sum_text = generate_summary(text)  # Generate summary of the recorded text
        yield "The summarized text is: " + sum_text 
        
        keywords = "Key points: " + top_frequent_words(text)  # Extract top keywords
        yield keywords        
        
        save_recording(text, sum_text, start_time)  # Save the recording

def listen_updates():
    """Alternative function to listen for voice commands and process them."""
    r = sr.Recognizer()
    text = ""
    with sr.Microphone() as source:
        print("Listening for command...")
        yield "Listening for command..."
        text_to_speech("Listening for command...")
        
        start_time = datetime.now()  # Capture the start time of the session
        print(f'The start time for the listening is: {start_time}\n')
        time_limit = timedelta(seconds=120)  # Set a time limit for command listening
    
        start_mode = None
        while flag:
            if datetime.now() - start_time >= time_limit:
                yield f"Time limit of {time_limit} seconds has been passed.\n"
                command_text = "Stop recording"
                command_process(command_text, text, start_time)
                final_text = "The recorded text is: " + text
                yield final_text
                sum_text = "The summarized text is: " + generate_summary(text)
                yield sum_text 
                keywords = top_frequent_words(text)
                yield keywords 

            audio = r.listen(source, phrase_time_limit=20)  # Listen to the command
            try:
                command_text = r.recognize_google(audio)  # Convert command to text
                command = command_process(command_text, text, start_time)  # Process the command
                if command == "start":
                    start_time = datetime.now()
                    yield 'Recording started.'
                    print(f'The start time of the recording is: {start_time}\n')
                    start_mode = 1
                elif command == "stop":
                    yield 'Recording stopped.'
                    print("The recorded text is: ", text)
                    final_text = "The recorded text is: " + text
                    yield final_text
                    sum_text = "The summarized text is: " + generate_summary(text) 
                    yield sum_text 
                    keywords = top_frequent_words(text)
                    yield keywords 
                elif start_mode:
                    text += " " + command_text
                    print("The recorded text is: ", text)
                    yield command_text
            except sr.UnknownValueError:
                yield "Could not understand audio"
            except sr.RequestError as e:
                yield f"Error: {e}"

                



