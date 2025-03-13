from flask import Flask, jsonify, request, render_template
import random
import os
import time
import threading
import cv2
from text2speach import speak_input
from llm_add import llm
from langchain_core.prompts import PromptTemplate
from Transcript import record_audio, transcribe_audio

app = Flask(__name__)

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

def start_video_recording():
    os.makedirs("videos", exist_ok=True)
    filename = f"videos/video.avi"
    cap = cv2.VideoCapture(0)
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
    return cap, out, filename

def record_audio_thread(audio_file, duration):
    record_audio(audio_file, duration=duration)

def recognize_speech(duration, cap=None, out=None):
    audio_file = "temp.wav"
    print("Processing recorded audio...")
    if cap is not None and out is not None:
        audio_thread = threading.Thread(target=record_audio_thread, args=(audio_file, duration))
        audio_thread.start()
        start_time = time.time()
        while time.time() - start_time < duration:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture video frame")
                break
            out.write(frame)
        audio_thread.join()
    else:
        record_audio(audio_file, duration=duration)
    text = transcribe_audio(audio_file)
    if os.path.exists(audio_file):
        os.remove(audio_file)
    return text if text else "No response"

def stop_video_recording(cap, out):
    if out is not None:
        out.release()
    if cap is not None:
        cap.release()

def keyword(text):
    text = text.lower()
    matched_keywords = [kw for kw in KEYWORD_LIST if kw in text]
    return matched_keywords if matched_keywords else ["general"]

def map_keywords_to_files(keywords):
    question_files = [f"question_set/{kw}.txt" for kw in keywords if os.path.exists(f"question_set/{kw}.txt")]
    return question_files if question_files else ["question_set/question.txt"]

def generate_correct_response(question, response):
    template = '''
    You are a question helper. You must check the response against the answer.
    
    If the answer is completely wrong, reply with a correct answer starting with 0.
    If the answer is correct, start with 1 (no need to reply further).
    If the answer is partially correct, start with 0.5 and provide a modified reply.

    Question: {question}
    Response: {response}

    Max word limit: 100. There may be some word discrepancy as we are detecting voice.
    '''
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    try:
        response = chain.invoke(input={"question": question, "response": response})
        return response.content
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Error processing response"

# Global state
question_sources = ["question.txt"]
cap, out, video_file = None, None, None
current_question_index = 0
recording_in_progress = False

@app.route('/')
def index():
    return render_template('interview.html')

@app.route('/start_interview', methods=['GET'])
def start_interview():
    global cap, out, video_file, current_question_index
    cap, out, video_file = start_video_recording()
    current_question_index = 0
    return get_next_question()

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global recording_in_progress
    recording_in_progress = True
    return jsonify({"status": "recording started"})

@app.route('/submit_audio', methods=['POST'])
def submit_audio():
    global cap, out
    audio_file = request.files.get('audio')
    if not audio_file:
        return jsonify({"error": "No audio file provided"}), 400
    
    # Save the audio file temporarily
    temp_audio_path = "temp_uploaded.wav"
    audio_file.save(temp_audio_path)
    
    # Transcribe the audio
    transcript = transcribe_audio(temp_audio_path)
    
    # Clean up
    if os.path.exists(temp_audio_path):
        os.remove(temp_audio_path)
    
    return jsonify({"transcript": transcript if transcript else "No speech detected"})

@app.route('/next_question', methods=['GET'])
def get_next_question():
    global current_question_index, question_sources
    if current_question_index >= 5:
        stop_video_recording(cap, out)
        return jsonify({"question": "Interview completed!", "video_file": video_file, "done": True})
    
    if current_question_index < 3:
        question = PERSONALITY_QUESTIONS[current_question_index]
    elif current_question_index == 3:
        question = "What topic do you think is your strong zone?"
    else:
        question_file = random.choice(question_sources)
        question = get_random_question(question_file) or "No questions available."
    
    current_question_index += 1
    speak_input(question)
    return jsonify({"question": question, "index": current_question_index, "done": False})

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    global question_sources, cap, out
    data = request.json
    question = data.get("question", "")
    index = data.get("index", 0)
    transcript = data.get("transcript", "No response")
    
    # Process the answer internally
    if index <= 3:
        if index == 3:
            keywords = keyword(transcript)
            question_sources = map_keywords_to_files(keywords)
            print(f"Keywords detected: {keywords}")
        return jsonify({"transcript": transcript, "next": True})
    else:
        feedback = generate_correct_response(question, transcript)
        print(f"Feedback for question {index}: {feedback}")
        return jsonify({"transcript": transcript, "next": True})

@app.route('/end_interview', methods=['GET'])
def end_interview():
    global cap, out, video_file
    stop_video_recording(cap, out)
    return jsonify({"message": "Interview ended", "video_file": video_file})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)