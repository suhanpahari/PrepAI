from flask import Flask, jsonify, request, render_template
import random
import os
import time
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.text2speach import speak_input
from src.llm_add import llm
from langchain_core.prompts import PromptTemplate
from src.Transcript import record_audio, transcribe_audio

app = Flask(__name__)

# Configuration
VIDEOS_DIR = "videos"
QUESTION_SETS_DIR = "question_set"
TEMP_AUDIO_FILE = "temp_uploaded.wav"
MAX_INTERVIEW_QUESTIONS = 5
EMAIL_SENDER = "paharisoham@yahoo.com"  # Replace with your Yahoo email
EMAIL_PASSWORD = "bcpbmskrrtooojdf"  # Replace with your Yahoo app-specific password
SMTP_SERVER = "smtp.mail.yahoo.com"
SMTP_PORT = 587
PREDEFINED_RECEIVER_EMAIL = "paharisoham@gmail.com"  # Replace with the predefined receiver's email

# Validate predefined email at startup
def is_valid_email(email):
    """Validate email format using a regular expression."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

if not is_valid_email(PREDEFINED_RECEIVER_EMAIL):
    raise ValueError(f"Invalid predefined receiver email: {PREDEFINED_RECEIVER_EMAIL}")

# Personality questions
PERSONALITY_QUESTIONS = [
    "Hello welcome to PrepAI Introduce yourself",
    # "Explain merge short",
    # "explain dynamic programming"
    
]

# Keywords for matching
KEYWORD_LIST = [
    "science", "math", "history", "literature", "technology", 
    "art", "music", "sports", "programming", "engineering"
]

# Global state
question_sources = ["question.txt"]
current_question_index = 0
user_responses = []  # Store user responses and feedback

# Helper functions
def get_random_question(filename="question.txt"):
    """Load and return a random question from the specified file."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            questions = [q.strip() for q in file.readlines() if q.strip()]
        return random.choice(questions) if questions else None
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return None

def record_audio_thread(audio_file, duration):
    """Record audio in a separate thread."""
    record_audio(audio_file, duration=duration)

def recognize_speech(duration):
    """Record and transcribe speech."""
    audio_file = "temp.wav"
    print("Processing recorded audio...")
    record_audio(audio_file, duration=duration)
    text = transcribe_audio(audio_file)
    if os.path.exists(audio_file):
        os.remove(audio_file)
    return text if text else "No response"

def extract_keywords(text):
    """Extract keywords from text."""
    text = text.lower()
    matched_keywords = [kw for kw in KEYWORD_LIST if kw in text]
    return matched_keywords if matched_keywords else ["general"]

def map_keywords_to_files(keywords):
    """Map keywords to question files."""
    question_files = [f"{QUESTION_SETS_DIR}/{kw}.txt" for kw in keywords 
                     if os.path.exists(f"{QUESTION_SETS_DIR}/{kw}.txt")]
    return question_files if question_files else [f"{QUESTION_SETS_DIR}/question.txt"]

def generate_correct_response(question, response):
    """Generate feedback for a response using LLM."""
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

def generate_ocean_score():
    """Generate a random OCEAN score."""
    return {
        "Openness": random.randint(30, 65),
        "Conscientiousness": random.randint(30, 65),
        "Extraversion": random.randint(30, 65),
        "Agreeableness": random.randint(30, 65),
        "Neuroticism": random.randint(30, 65)
    }

def send_email(recipient_email, responses, ocean_score):
    """Send an email with the user's responses and OCEAN score."""
    try:
        # Set up the MIME
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient_email
        msg['Subject'] = "Your Interview Responses and OCEAN Score"

        # Create the email body
        body = "Thank you for completing the interview! Below are your responses and feedback:\n\n"
        for idx, res in enumerate(responses, 1):
            body += f"Question {idx}: {res['question']}\n"
            body += f"Your Response: {res['transcript']}\n"
            body += f"Feedback: {res['feedback']}\n\n"
        
        body += "Your OCEAN Personality Score:\n"
        for trait, score in ocean_score.items():
            body += f"{trait}: {score}\n"

        msg.attach(MIMEText(body, 'plain'))

        # Connect to the SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, recipient_email, msg.as_string())
        server.quit()
        print(f"Email sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
        raise

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login.html', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/pricing.html')
def pricing():
    return render_template('pricing.html')

@app.route('/verification.html')
def verification():
    return render_template('verification.html')

@app.route('/interview.html')
def interview():
    return render_template('interview.html')

@app.route('/start_interview', methods=['GET'])
def start_interview():
    """Initialize and start a new interview session."""
    global current_question_index, user_responses
    current_question_index = 0
    user_responses = []  # Reset responses
    
    # Ensure videos directory exists
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    
    return get_next_question()

@app.route('/start_recording', methods=['POST'])
def start_recording():
    """Mark the beginning of audio/video recording."""
    return jsonify({"status": "recording started"})

@app.route('/submit_audio', methods=['POST'])
def submit_audio():
    """Process submitted audio and return the transcript."""
    audio_file = request.files.get('audio')
    if not audio_file:
        return jsonify({"error": "No audio file provided"}), 400
    
    # Save the audio file temporarily
    temp_audio_path = TEMP_AUDIO_FILE
    audio_file.save(temp_audio_path)
    
    # Transcribe the audio
    transcript = transcribe_audio(temp_audio_path)
    
    # Clean up
    if os.path.exists(temp_audio_path):
        os.remove(temp_audio_path)
    
    return jsonify({"transcript": transcript if transcript else "No speech detected"})

@app.route('/next_question', methods=['GET'])
def get_next_question():
    """Get the next interview question."""
    global current_question_index, question_sources
    
    # Check if we've reached the end of the interview
    if current_question_index >= MAX_INTERVIEW_QUESTIONS:
        return jsonify({
            "question": "Interview completed!", 
            "done": True
        })
    
    # Select appropriate question based on current stage
    if current_question_index < 1:
        question = PERSONALITY_QUESTIONS[current_question_index]
    elif current_question_index == 1:
        question = "What topic do you think is your strong zone?"
    else:
        question_file = random.choice(question_sources)
        question = get_random_question(question_file) or "No questions available."
    
    # Increment counter and speak the question
    current_question_index += 1
    speak_input(question)
    
    return jsonify({
        "question": question, 
        "index": current_question_index, 
        "done": False
    })

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Process the submitted answer."""
    global question_sources, user_responses
    data = request.json
    question = data.get("question", "")
    index = data.get("index", 0)
    transcript = data.get("transcript", "No response")
    
    # Process the answer internally
    feedback = "No feedback for personality questions."
    if index <= 1:
        # For personality questions and strong zone question
        if index == 1:
            # Extract keywords from the response to determine question topic
            keywords = extract_keywords(transcript)
            question_sources = map_keywords_to_files(keywords)
            print(f"Keywords detected: {keywords}")
    else:
        # For knowledge-based questions
        feedback = generate_correct_response(question, transcript)
        print(f"Feedback for question {index}: {feedback}")
    
    # Store the response
    user_responses.append({
        "question": question,
        "transcript": transcript,
        "feedback": feedback
    })
    
    return jsonify({"transcript": transcript, "next": True})

@app.route('/end_interview', methods=['GET'])
def end_interview():
    """End the interview session and send email to predefined receiver."""
    global user_responses
    if not user_responses:
        return jsonify({"message": "Interview ended, but no responses available"}), 400
    
    try:
        ocean_score = generate_ocean_score()
        send_email(PREDEFINED_RECEIVER_EMAIL, user_responses, ocean_score)
        print(f"Sent interview summary to {PREDEFINED_RECEIVER_EMAIL}")
        return jsonify({"message": "Interview ended, email sent to predefined receiver"})
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

@app.route('/save_video', methods=['POST'])
def save_video():
    """Save the video file sent from the client."""
    try:
        # Create videos directory if it doesn't exist
        os.makedirs(VIDEOS_DIR, exist_ok=True)
        video_file = request.files.get('video')
        mime_type = request.form.get('mime_type', 'video/webm')
        
        if not video_file:
            print("Error: No video file received in request")
            return jsonify({"success": False, "error": "No video file received"}), 400
        
        # Determine file extension based on MIME type
        extension_map = {
            'video/webm': 'webm',
            'video/mp4': 'mp4',
            'video/avi': 'avi'
        }
        
        # Default to webm if the MIME type is not recognized
        file_extension = extension_map.get(mime_type, 'webm')
        print(f"Received video with MIME type: {mime_type}, using extension: {file_extension}")
        
        # Save the original file
        timestamp = int(time.time())
        original_filename = f"{VIDEOS_DIR}/video_{timestamp}.{file_extension}"
        video_file.save(original_filename)
        print(f"Original video saved as {original_filename}")
        
        # Target format - change this to your preferred format
        target_format = 'avi'  # or 'mp4'
        output_filename = f"{VIDEOS_DIR}/video_{timestamp}.{target_format}"
        
        # Only convert if the original format is different from the target
        if file_extension != target_format:
            try:
                # Check if ffmpeg is available
                ffmpeg_result = os.system("which ffmpeg > /dev/null 2>&1")
                
                if ffmpeg_result == 0:  # ffmpeg is available
                    print(f"Converting {original_filename} to {output_filename}")
                    # Use appropriate conversion parameters based on target format
                    if target_format == 'avi':
                        conversion_cmd = f"ffmpeg -i {original_filename} -c:v libxvid -q:v 6 -c:a libmp3lame {output_filename}"
                    else:  # mp4
                        conversion_cmd = f"ffmpeg -i {original_filename} -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k {output_filename}"
                    
                    os.system(conversion_cmd)
                    
                    # Check if conversion was successful
                    if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                        print(f"Successfully converted video to {target_format}")
                        return jsonify({
                            "success": True, 
                            "filename": output_filename, 
                            "original": original_filename
                        })
                    else:
                        print(f"Conversion failed or output file is empty, using original format")
                        return jsonify({
                            "success": True, 
                            "filename": original_filename
                        })
                else:
                    print("ffmpeg not available, using original format")
                    return jsonify({
                        "success": True, 
                        "filename": original_filename
                    })
            except Exception as e:
                print(f"Error during conversion: {e}")
                return jsonify({
                    "success": True, 
                    "filename": original_filename, 
                    "conversion_error": str(e)
                })
        else:
            # No conversion needed
            return jsonify({
                "success": True, 
                "filename": original_filename
            })
        
    except Exception as e:
        print(f"Error processing video: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)