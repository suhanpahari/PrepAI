import random
import os
from datetime import datetime
from text2speach import speak_input
from llm_add import llm
from langchain_core.prompts import PromptTemplate
from Transcript import record_audio, transcribe_audio
import cv2
import time
import threading  

# Define some personality-based questions
PERSONALITY_QUESTIONS = [
    "What motivates you to work hard?",
    "Describe a challenge you've faced and how you overcame it.",
    "How do you handle feedback?"
]

# Function to get a random question from a file
def get_random_question(filename="question.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            questions = [q.strip() for q in file.readlines() if q.strip()]
        return random.choice(questions) if questions else None
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return None

# Start video recording function
def start_video_recording():
    os.makedirs("videos", exist_ok=True)
    
    filename = f"videos/video.avi"
    
    cap = cv2.VideoCapture(0)  # Default webcam
    if not cap.isOpened():
        print("Error: Could not open video device")
        return None, None, None
    
    # Define video codec and create writer
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
    
    if not out.isOpened():
        print("Error: Could not create video writer")
        cap.release()
        return None, None, None
    
    print(f"Started video recording to {filename}")
    return cap, out, filename

# Audio recording in a separate thread
def record_audio_thread(audio_file, duration):
    record_audio(audio_file, duration=duration)

# Speech recognition and synchronized recording
def recognize_speech(duration=5, cap=None, out=None):
    audio_file = "temp.wav"
    print("Listening... Speak now.")
    
    try:
        if cap is not None and out is not None:
            # Start audio recording in a separate thread
            audio_thread = threading.Thread(target=record_audio_thread, args=(audio_file, duration))
            audio_thread.start()
            
            start_time = time.time()
            while time.time() - start_time < duration:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Failed to capture video frame")
                    break
                
                out.write(frame)
                cv2.imshow('Recording', frame)
                
                # Allow early exit with 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            audio_thread.join()  # Ensure audio recording completes
            
            cv2.destroyAllWindows()
        else:
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
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)  # Clean up temp file

# Stop video recording
def stop_video_recording(cap, out):
    if out is not None:
        out.release()
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("Video recording stopped")

# Main function
def main():
    name = input("Enter your name: ")
    participant_id = input("Enter your ID: ")

    start = input("Start? (y/n): ").strip().lower()
    if start != "y":
        print("Exiting...")
        return

    question_sources = ["question.txt"]

    # Start **one** continuous video recording
    cap, out, video_file = start_video_recording()

    try:
        for i in range(5):  # Loop through 5 questions
            print(f"\nQuestion {i + 1}:")
            
            # Select a question
            if i < 3:
                question = PERSONALITY_QUESTIONS[i]
            elif i == 3:
                question = "What topic do you think is your strong zone?"
            else:
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

            # Recognize speech while video recording continues
            answer = recognize_speech(duration=15, cap=cap, out=out)

            print(f"Answer {i + 1}: {answer}")

            time.sleep(2)  # Pause before next question

    except KeyboardInterrupt:
        print("\nSession interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Stop video recording **once** at the end
        stop_video_recording(cap, out)
        print(f"Session completed. Video saved to {video_file}")




if __name__ == "__main__":
    main()
