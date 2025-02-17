import speech_recognition as sr

def listen(language_code):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak now...")
        audio = recognizer.listen(source)
        try:
            return recognizer.recognize_google(audio, language=language_code)
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
            return ""
        except sr.RequestError:
            print("Sorry, there was an issue with the request.")
            return ""

if __name__ == "__main__":
    lang_code = "en-US"
    lang_name = "English (United States)"
    
    print(f"Listening in {lang_name} ({lang_code})...\n")
    
    while True:
        command = listen(lang_code)
        if command:
            print(f"You said: {command}")
        
        # Add a condition to break the loop if needed
        if command.lower() == "exit":
            print("Exiting...")
            break