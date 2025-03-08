import random
import subprocess
import platform
from text2speach import speak_input
from llm_add import llm
from langchain_core.prompts import PromptTemplate
from Transcript import record_audio, transcribe_audio
import cv2  # For video recording
import os
from datetime import datetime

# Fixed personality-based questions
PERSONALITY_QUESTIONS = [
    "How would you describe your approach to solving problems?",
    "Do you prefer working alone or in a team, and why?",
    "What motivates you to do your best work?"
]

# List of predefined keywords for matching
KEYWORD_LIST = [
    "science", "math", "history", "literature", "technology", 
    "art", "music", "sports", "programming", "engineering"
]

def get_random_question(filename="question.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            questions = [q.strip() for q in file.readlines() if q.strip()]
        return random.choice(questions) if questions else None
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return None

def recognize_speech(duration=15):
    audio_file = "temp.wav"
    print("Listening... Speak now.")
    try:
        record_audio(audio_file, duration=duration)
        print("Processing speech...")
        text = transcribe_audio(audio_file)
        if not text:
            print("No speech detected or transcription failed.")
            return "No response"
        return text
    except Exception as e:
        print(f"Error in transcription: {e}")
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

def start_video_recording(participant_id, question_num):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"video_{participant_id}_q{question_num}_{timestamp}.avi"
    cap = cv2.VideoCapture(0)  # Default webcam
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
    return cap, out, filename

def stop_video_recording(cap, out):
    cap.release()
    out.release()
    cv2.destroyAllWindows()

def keyword(text):
    text = text.lower()
    matched_keywords = [kw for kw in KEYWORD_LIST if kw in text]
    return matched_keywords if matched_keywords else ["general"]  # Default to "general" if no match

def map_keywords_to_files(keywords):
    question_files = []
    for kw in keywords:
        filename = f"{kw}.txt"
        if os.path.exists(filename):
            question_files.append(filename)
    return question_files if question_files else ["question.txt"]  # Fallback to default file

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
        print(f"Error generating response: {e}")
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

    question_sources = None  # Will be set after 4th question

    try:
        for i in range(5):
            print(f"\nQuestion {i + 1}:")
            
            # First 3 questions are personality-based
            if i < 3:
                question = PERSONALITY_QUESTIONS[i]
                print(question)
                speak_input(question)

                ready = input("Ready to answer? (y/n): ").strip().lower()
                if ready != "y":
                    print("Skipping question...")
                    continue

                # Start video recording
                cap, out, video_file = start_video_recording(participant_id, i + 1)
                print(f"Recording video to {video_file}...")

                answer = recognize_speech()
                print(f"Answer {i + 1}: {answer}")

                # Stop video recording
                stop_video_recording(cap, out)

                disaster_response = generate_currect_response(question, answer)
                print("Evaluation:", disaster_response)

            # 4th question: Strong zone
            elif i == 3:
                question = "What topic do you think is your strong zone?"
                print(question)
                speak_input(question)

                ready = input("Ready to answer? (y/n): ").strip().lower()
                if ready != "y":
                    print("Skipping question...")
                    question_sources = ["question.txt"]  # Default fallback
                    continue

                answer = recognize_speech()
                print(f"Answer {i + 1}: {answer}")

                # Process strong zone response
                keywords = keyword(answer)
                print(f"Extracted keywords: {keywords}")
                question_sources = map_keywords_to_files(keywords)
                print(f"Question sources for next question: {question_sources}")

            # 5th question: Based on strong zone
            else:
                if not question_sources:
                    question_sources = ["question.txt"]  # Fallback
                question_file = random.choice(question_sources)
                question = get_random_question(question_file)
                if not question:
                    print(f"No questions available in {question_file}. Exiting.")
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