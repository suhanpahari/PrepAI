import random
import os
import time
import threading
import cv2
from datetime import datetime
from text2speach import speak_input
from llm_add import llm
from langchain_core.prompts import PromptTemplate
from Transcript import record_audio, transcribe_audio

# Personality questions
PERSONALITY_QUESTIONS = [
    "How would you describe your approach to solving problems?",
    "Do you prefer working alone or in a team, and why?",
    "What motivates you to do your best work?"
]

# Keywords for matching
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

def start_video_recording(participant_id):
    """Start a single continuous video recording"""
    os.makedirs("videos", exist_ok=True)
    filename = f"videos/{participant_id}_session.avi"
    
    cap = cv2.VideoCapture(0)  # Open webcam
    if not cap.isOpened():
        print("Error: Could not open video device")
        return None, None, None

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))

    if not out.isOpened():
        print("Error: Could not create video writer")
        cap.release()
        return None, None, None
    
    print(f"Started video recording: {filename}")
    return cap, out, filename

def stop_video_recording(cap, out):
    """Stop video recording"""
    if out is not None:
        out.release()
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("Video recording stopped")

def record_audio_thread(audio_file, duration):
    """Record audio in a separate thread"""
    record_audio(audio_file, duration=duration)

def recognize_speech(duration=15, cap=None, out=None):
    """Recognize speech while recording video (if available)"""
    audio_file = "temp.wav"
    print("Listening... Speak now.")

    try:
        # Start audio recording in a separate thread
        audio_thread = threading.Thread(target=record_audio_thread, args=(audio_file, duration))
        audio_thread.start()

        start_time = time.time()
        while time.time() - start_time < duration:
            if cap and out:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Failed to capture video frame")
                    break
                out.write(frame)
                cv2.imshow('Recording', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        audio_thread.join()  # Wait for audio recording to complete
        cv2.destroyAllWindows()

        print("Processing speech...")
        text = transcribe_audio(audio_file)
        os.remove(audio_file)  # Clean up temp file

        return text if text else "No response"
    except Exception as e:
        print(f"Error in transcription: {e}")
        return "Error in recognition"

def keyword(text):
    """Extract keywords from response"""
    text = text.lower()
    matched_keywords = [kw for kw in KEYWORD_LIST if kw in text]
    return matched_keywords if matched_keywords else ["general"]

def map_keywords_to_files(keywords):
    """Map extracted keywords to question files"""
    question_files = [f"{kw}.txt" for kw in keywords if os.path.exists(f"{kw}.txt")]
    return question_files if question_files else ["question.txt"]

def generate_correct_response(question, response):
    """Evaluate the response correctness"""
    template = '''
    You are a question helper. You must check the response against the answer.
    
    If the answer is completely wrong, reply with a correct answer starting with 0.
    If the answer is correct, start with 1 (no need to reply further).
    If the answer is partially correct, start with 0.5 and provide a modified reply.

    Question: {question}
    Response: {response}

    Max word limit: 100. There may be some word discrepancy as we are 
    detecting voice. Consider that.
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
    """Main function to run the interview session"""
    name = input("Enter your name: ")
    participant_id = input("Enter your ID: ")

    start = input("Start? (y/n): ").strip().lower()
    if start != "y":
        print("Exiting...")
        return

    print("Eye and face tracking disabled.")
    
    question_sources = None
    cap, out, video_file = start_video_recording(participant_id)  # Start one continuous recording

    try:
        for i in range(5):
            print(f"\nQuestion {i + 1}:")

            if i < 3:
                question = PERSONALITY_QUESTIONS[i]
            elif i == 3:
                question = "What topic do you think is your strong zone?"
            else:
                if not question_sources:
                    question_sources = ["question.txt"]
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

            if i < 3:
                print("Personality question - no evaluation performed.")
            elif i == 3:
                keywords = keyword(answer)
                print(f"Extracted keywords: {keywords}")
                question_sources = map_keywords_to_files(keywords)
                print(f"Question sources for next question: {question_sources}")
            else:
                disaster_response = generate_correct_response(question, answer)
                print("Evaluation:", disaster_response)

    except KeyboardInterrupt:
        print("\nSession interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        stop_video_recording(cap, out)  # Stop recording at the end
        print(f"Session completed. Video saved to {video_file}")

if __name__ == "__main__":
    main()
