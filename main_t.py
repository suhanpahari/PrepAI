import pyaudio
import webrtcvad
import numpy as np
import wave
import tempfile
import os
import asyncio
import logging
import struct
import random
from groq import Groq
from elevenlabs.client import AsyncElevenLabs
from pygame import mixer
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
QUESTION_SETS_DIR = "question_set"
MAX_INTERVIEW_QUESTIONS = 5
PERSONALITY_QUESTIONS = [
    "How would you describe your approach to solving problems?",
    "Do you prefer working alone or in a team, and why?",
    "What motivates you to do your best work?"
]
KEYWORD_LIST = [
    "science", "math", "history", "literature", "technology",
    "art", "music", "sports", "programming", "engineering"
]

# Get API keys from environment variables with fallback to hardcoded values
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_a02661bc72a15d32268f049f94708c0b76433c20b0f2e403")
# Initialize clients
groq_client = Groq(api_key=GROQ_API_KEY)
elevenlabs_client = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)

class VoiceDetector:
    def __init__(self, sample_rate=16000, frame_duration_ms=30, min_speech_frames=10, max_silence_frames=50):
        self.vad = webrtcvad.Vad(3)
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.min_speech_frames = min_speech_frames
        self.max_silence_frames = max_silence_frames
        self.speech_frames = 0
        self.silence_frames = 0
        self.is_speaking = False

    def detect_voice(self, audio_data):
        try:
            if not audio_data or len(audio_data) == 0:
                logger.warning("Empty audio data")
                return False
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            if len(audio_array) == 0:
                logger.warning("No valid audio data after conversion")
                return False
            frames = [audio_array[i:i + self.frame_size] for i in range(0, len(audio_array), self.frame_size)]
            if not frames:
                logger.warning("No frames generated")
                return False
            current_speech_frames = 0
            for frame in frames:
                if len(frame) != self.frame_size:
                    continue
                frame_bytes = struct.pack("%dh" % len(frame), *frame)
                if self.vad.is_speech(frame_bytes, self.sample_rate):
                    current_speech_frames += 1
                    self.speech_frames += 1
                    self.silence_frames = 0
                else:
                    self.silence_frames += 1
            if current_speech_frames > 0:
                if not self.is_speaking and self.speech_frames >= self.min_speech_frames:
                    self.is_speaking = True
                return True
            elif self.silence_frames > self.max_silence_frames:
                if self.is_speaking:
                    self.is_speaking = False
                    self.speech_frames = 0
                return False
            return self.is_speaking
        except Exception as e:
            logger.error(f"Voice detection error: {str(e)}")
            return False

async def transcribe_audio(audio_data: bytes):
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_wav.write(audio_data)
            temp_path = temp_wav.name

        # Ensure file is closed before using it
        with open(temp_path, 'rb') as audio_file:
            response = groq_client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                response_format="text"
            )
        
        os.unlink(temp_path)
        return response
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return None


async def generate_response(text: str):
    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful interview assistant. Provide concise responses (max 2 sentences)."},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=100
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Chat response error: {str(e)}")
        return None

async def generate_feedback(question: str, response: str):
    try:
        template = '''
        You are a question helper. Check the response against the question.

        If the answer is completely wrong, reply with a correct answer starting with "0".
        If the answer is correct, reply with "1".
        If the answer is partially correct, start with "0.5" and provide a modified reply.

        Question: {question}
        Response: {response}

        Max word limit: 100. Account for potential transcription discrepancies.
        '''
        prompt = template.format(question=question, response=response)
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an interview feedback assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Feedback generation error: {str(e)}")
        return None

async def generate_speech(text: str):
    try:
        response_gen = elevenlabs_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",  # Alloy voice
            text=text,
            model_id="eleven_monolingual_v1"
        )
        audio_data = b""
        async for chunk in response_gen:
            audio_data += chunk
        return audio_data
    except Exception as e:
        logger.error(f"Speech generation error: {str(e)}")
        return None


async def play_audio(audio_data: bytes):
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
            temp_mp3.write(audio_data)
            temp_mp3.flush()
            mixer.init()
            mixer.music.load(temp_mp3.name)
            mixer.music.play()
            while mixer.music.get_busy():
                await asyncio.sleep(0.1)
            mixer.quit()
            os.unlink(temp_mp3.name)
    except Exception as e:
        logger.error(f"Audio playback error: {str(e)}")

def get_random_question(filename="question.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            questions = [q.strip() for q in file.readlines() if q.strip()]
        return random.choice(questions) if questions else None
    except FileNotFoundError:
        logger.error(f"Question file {filename} not found")
        return None

def extract_keywords(text):
    text = text.lower()
    matched_keywords = [kw for kw in KEYWORD_LIST if kw in text]
    return matched_keywords if matched_keywords else ["general"]

def map_keywords_to_files(keywords):
    question_files = [f"{QUESTION_SETS_DIR}/{kw}.txt" for kw in keywords
                     if os.path.exists(f"{QUESTION_SETS_DIR}/{kw}.txt")]
    return question_files if question_files else [f"{QUESTION_SETS_DIR}/question.txt"]

async def main():
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024
    )
    voice_detector = VoiceDetector()
    audio_buffer = bytearray()
    is_responding = False
    current_question_index = 0
    question_sources = [f"{QUESTION_SETS_DIR}/question.txt"]

    print("Interview Assistant started. Answer questions when prompted. Press Ctrl+C to exit.")

    # Startup message
    startup_message = "Welcome to the interview. I'll ask you a series of questions. Please answer clearly and wait for silence to hear the next question."
    audio_data = await generate_speech(startup_message)
    await play_audio(audio_data)

    try:
        while current_question_index < MAX_INTERVIEW_QUESTIONS:
            # Select question
            if current_question_index < 3:
                question = PERSONALITY_QUESTIONS[current_question_index]
            elif current_question_index == 3:
                question = "What topic do you think is your strong zone?"
            else:
                question_file = random.choice(question_sources)
                question = get_random_question(question_file) or "No questions available."

            # Speak question
            print(f"\nQuestion {current_question_index + 1}: {question}")
            audio_data = await generate_speech(question)
            await play_audio(audio_data)

            current_question_index += 1
            audio_buffer.clear()

            # Listen for response
            while True:
                data = stream.read(1024, exception_on_overflow=False)
                voice_detected = voice_detector.detect_voice(data)

                print(f"\r{'Listening...' if voice_detected else 'Waiting for your answer...'}", end="")

                if voice_detected:
                    audio_buffer.extend(data)
                    if is_responding:
                        is_responding = False
                        mixer.music.stop()
                        print("\nResponse interrupted.")
                else:
                    if len(audio_buffer) > 0 and voice_detector.silence_frames >= voice_detector.max_silence_frames and not is_responding:
                        print("\nProcessing answer...")
                        transcription = await transcribe_audio(bytes(audio_buffer))
                        audio_buffer.clear()

                        if transcription:
                            print(f"Your answer: {transcription}")

                            # Process answer
                            if current_question_index <= 3:
                                if current_question_index == 3:
                                    keywords = extract_keywords(transcription)
                                    question_sources = map_keywords_to_files(keywords)
                                    print(f"Keywords detected: {keywords}")
                            else:
                                feedback = await generate_feedback(question, transcription)
                                if feedback:
                                    print(f"Feedback: {feedback}")
                                    audio_data = await generate_speech(feedback)
                                    is_responding = True
                                    await play_audio(audio_data)
                                    is_responding = False

                            break
                        else:
                            error_message = "I couldn't understand your answer. Please try again."
                            print(error_message)
                            audio_data = await generate_speech(error_message)
                            is_responding = True
                            await play_audio(audio_data)
                            is_responding = False
                            audio_buffer.clear()

        # Interview completed
        completion_message = "Interview completed. Thank you for participating!"
        print(f"\n{completion_message}")
        audio_data = await generate_speech(completion_message)
        await play_audio(audio_data)

    except KeyboardInterrupt:
        print("\nExiting...")
        goodbye_message = "Interview terminated. Goodbye!"
        audio_data = await generate_speech(goodbye_message)
        await play_audio(audio_data)
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLI Interview Assistant using Groq and ElevenLabs")
    args = parser.parse_args()
    asyncio.run(main())