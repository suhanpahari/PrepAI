import random
import subprocess
import signal
import speech_recognition as sr
from text2speach import speak_input  # Importing speak_input function from text2speech.py
import platform

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

# Function to start eye tracking in a new window
def start_eye_tracking():
    if platform.system() == "Windows":
        # For Windows, use 'start' to open a new terminal window
        return subprocess.Popen(["start", "python", "eye.py"], shell=True)
    elif platform.system() == "Darwin":  # macOS
        # For macOS, use 'open' with a new Terminal window
        return subprocess.Popen(["open", "-a", "Terminal", "python", "eye.py"])
    elif platform.system() == "Linux":
        # For Linux, use 'gnome-terminal' or 'xterm'
        return subprocess.Popen(["gnome-terminal", "--", "python", "eye.py"])
    else:
        raise OSError("Unsupported operating system")

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

    # Run eye.py in a new window
    print("Starting eye tracking in a new window...")
    eye_tracking_process = start_eye_tracking()

    try:
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

    except KeyboardInterrupt:
        print("\nSession interrupted by user.")

    finally:
        # Terminate eye tracking process properly
        print("\nStopping eye tracking...")
        eye_tracking_process.terminate()  # Graceful termination
        eye_tracking_process.wait()  # Wait for termination
        print("Session completed.")

if __name__ == "__main__":
    main()