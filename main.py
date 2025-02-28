import random
import subprocess
import time
import speech_recognition as sr
from text2speach import speak_input  # Importing speak_input function from text2speech.py

# Function to pick a random question
def get_random_question(filename="question.txt"):
    with open(filename, "r", encoding="utf-8") as file:
        questions = [q.strip() for q in file.readlines() if q.strip()]
    return random.choice(questions) if questions else None

# Function to recognize speech with a 5-second silence timeout
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Speak now.")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)  # Max 15 sec per answer
            print("Processing speech...")
            text = recognizer.recognize_google(audio)  # Convert speech to text
            return text
        except sr.WaitTimeoutError:
            print("No speech detected.")
            return "No response"
        except sr.UnknownValueError:
            print("Could not understand the response.")
            return "Unclear response"
        except sr.RequestError:
            print("Speech recognition service error.")
            return "Error in recognition"

# Main function
def main():
    # Get participant details
    name = input("Enter your name: ")
    participant_id = input("Enter your ID: ")

    # Ask if they are ready
    start = input("Start? (y/n): ").strip().lower()
    if start != "y":
        print("Exiting...")
        return

    # Run eye.py in the background
    print("Starting eye tracking...")
    eye_tracking_process = subprocess.Popen(["python", "eye.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Ask 5 questions
    for i in range(5):
        print(f"\nQuestion {i + 1}:")
        
        question = get_random_question()
        if not question:
            print("No questions available. Exiting.")
            break

        print(question)
        speak_input(question)  # Convert question to speech

        # Ask if ready to answer
        ready = input("Ready to answer? (y/n): ").strip().lower()
        if ready != "y":
            print("Skipping question...")
            continue

        # Start speech recognition
        answer = recognize_speech()
        print(f"Answer {i + 1}: {answer}")

    # Terminate eye tracking
    print("\nStopping eye tracking...")
    eye_tracking_process.terminate()
    print("Session completed.")

if __name__ == "__main__":
    main()