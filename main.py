import random
import subprocess
import speech_recognition as sr
from text2speach import speak_input
import platform
from llm_add import llm
from langchain_core.prompts import PromptTemplate

def get_random_question(filename="question.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            questions = [q.strip() for q in file.readlines() if q.strip()]
        return random.choice(questions) if questions else None
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return None

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Speak now.")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            print("Processing speech...")
            text = recognizer.recognize_google(audio)
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

def start_eye_tracking():
    try:
        if platform.system() == "Windows":
            return subprocess.Popen(["start", "cmd", "/c", "python", "eye.py"], shell=True)
        elif platform.system() == "Darwin":
            return subprocess.Popen(["open", "-a", "Terminal", "python", "eye.py"])
        elif platform.system() == "Linux":
            return subprocess.Popen(["gnome-terminal", "--", "python", "eye.py"])
        else:
            raise OSError("Unsupported operating system")
    except Exception as e:
        print(f"Error starting eye tracking: {e}")
        return None

def start_face_tracking():
    try:
        if platform.system() == "Windows":
            return subprocess.Popen(["start", "cmd", "/c", "python", "face.py"], shell=True)
        elif platform.system() == "Darwin":
            return subprocess.Popen(["open", "-a", "Terminal", "python", "face.py"])
        elif platform.system() == "Linux":
            return subprocess.Popen(["gnome-terminal", "--", "python", "face.py"])
        else:
            raise OSError("Unsupported operating system")
    except Exception as e:
        print(f"Error starting face tracking: {e}")
        return None

def generate_currect_response(question, response):
    template = '''
    You are a question helper. You must check the response against the answer.
    
    If the answer is completely wrong, reply with a correct answer starting with 0.
    If the answer is correct, start with 1 (no need to reply further).
    If the answer is partially correct, start with 0.5 and provide a modified reply.

    Question: {question}
    Response: {response}

    Max word limit: 100. there may be some word discrepancy as we are 
    detecting voice. consider that.
    '''
    
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    
    try:
        response = chain.invoke(input={"question": question, "response": response})
        return response.content
    except Exception as e:
        print(f"Error generating disaster response: {e}")
        return "Error processing response"

def main():
    name = input("Enter your name: ")
    participant_id = input("Enter your ID: ")

    start = input("Start? (y/n): ").strip().lower()
    if start != "y":
        print("Exiting...")
        return

    print("Starting eye and face tracking in new windows...")
    eye_tracking_process = start_eye_tracking()
    face_tracking_process = start_face_tracking()

    try:
        for i in range(5):
            print(f"\nQuestion {i + 1}:")
            
            question = get_random_question()
            if not question:
                print("No questions available. Exiting.")
                break

            print(question)
            speak_input(question)

            ready = input("Ready to answer? (y/n): ").strip().lower()
            if ready != "y":
                print("Skipping question...")
                continue

            answer = recognize_speech()
            print(f"Answer {i + 1}: {answer}")

            disaster_response = generate_currect_response(question, answer)
            print("Evaluation:", disaster_response)

    except KeyboardInterrupt:
        print("\nSession interrupted by user.")

    finally:
        print("\nStopping tracking processes...")
        if eye_tracking_process:
            eye_tracking_process.terminate()
        if face_tracking_process:
            face_tracking_process.terminate()
        
        if eye_tracking_process:
            eye_tracking_process.wait()
        if face_tracking_process:
            face_tracking_process.wait()
        
        print("Session completed.")

if __name__ == "__main__":
    main()