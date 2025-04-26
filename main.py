import random
import os
import json

from text2speach import speak_input
from Transcript import transcribe_audio
#from llm_add import llm

# CONFIG
MAX_INTERVIEW_QUESTIONS = 5
QUESTION_SETS_DIR = "question_set"
KEYWORD_LIST = ["science", "math", "history", "literature", "technology", 
                "art", "music", "sports", "programming", "engineering"]

PERSONALITY_QUESTIONS = [
    "How would you describe your approach to solving problems?",
    "Do you prefer working alone or in a team, and why?",
    "What motivates you to do your best work?"
]

# ------------------------
def get_random_question(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        return random.choice(lines) if lines else None
    except FileNotFoundError:
        print(f"[!] File not found: {filename}")
        return None

def extract_keywords(text):
    text = text.lower()
    return [kw for kw in KEYWORD_LIST if kw in text] or ["general"]

def map_keywords_to_files(keywords):
    files = [f"{QUESTION_SETS_DIR}/{kw}.txt" for kw in keywords 
             if os.path.exists(f"{QUESTION_SETS_DIR}/{kw}.txt")]
    return files or [f"{QUESTION_SETS_DIR}/question.txt"]

def split_transcript(transcript, n):
    words = transcript.split()
    seg_len = len(words) // n
    return [
        " ".join(words[i * seg_len: None if i == n - 1 else (i + 1) * seg_len])
        for i in range(n)
    ]

def generate_fake_transcript(questions):
    print("\nPlease type your answer for each question below.\n")
    responses = []
    for q in questions:
        print(f"Q: {q}")
        ans = input("A: ")
        responses.append(ans)
    return " ".join(responses)

def generate_interview_analysis(transcript):
    # Replace this with real LLM chain if available
    return "[FAKE ANALYSIS]\nGood responses overall. Try to elaborate more on specific achievements.\n"

# ------------------------
def run_cli_interview():
    questions = []
    
    print("🚀 Starting Interview...\n")

    # Ask 3 personality questions
    for i in range(3):
        q = PERSONALITY_QUESTIONS[i]
        questions.append(q)

    # Ask about strong zone
    strong_zone_q = "What topic do you think is your strong zone?"
    print(f"Q4: {strong_zone_q}")
    zone = input("A4: ")
    questions.append(strong_zone_q)

    # Map keywords from answer to files
    keywords = extract_keywords(zone)
    files = map_keywords_to_files(keywords)

    # Final question from keyword set
    q_file = random.choice(files)
    q = get_random_question(q_file) or "Tell us something interesting about your field."
    questions.append(q)

    # Simulate full transcript
    transcript_text = generate_fake_transcript(questions)
    segments = split_transcript(transcript_text, len(questions))

    formatted_transcript = ""
    for i, (q, a) in enumerate(zip(questions, segments)):
        formatted_transcript += f"Question {i+1}: {q}\nAnswer: {a}\n\n"

    print("\n📝 Formatted Transcript:\n")
    print(formatted_transcript)

    analysis = generate_interview_analysis(transcript_text)
    print("\n📊 Interview Analysis:\n")
    print(analysis)

# ------------------------
if __name__ == "__main__":
    run_cli_interview()
