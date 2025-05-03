import asyncio
import base64
import cv2
import os
import pyaudio
import requests
import json
from threading import Lock, Thread
from cv2 import VideoCapture, imencode
from dotenv import load_dotenv

load_dotenv()

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_TTS_URL = "https://api.groq.com/openai/v1/audio/speech"
LLAMA4_MODEL = "llama-4-scout-17b-16e-instruct"

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5  # Duration for audio capture

# System prompt
SYSTEM_PROMPT = """
You are a witty assistant that uses chat history and user-provided images to answer questions.
Use few words in your answers. Go straight to the point. Do not use emoticons or emojis.
Be friendly and helpful. Show some personality.
"""

class WebcamStream:
    def __init__(self):
        self.stream = VideoCapture(index=0)
        _, self.frame = self.stream.read()
        self.running = False
        self.lock = Lock()

    def start(self):
        if self.running:
            return self
        self.running = True
        self.thread = Thread(target=self.update, args=())
        self.thread.start()
        return self

    def update(self):
        while self.running:
            _, frame = self.stream.read()
            self.lock.acquire()
            self.frame = frame
            self.lock.release()

    def read(self, encode=False):
        self.lock.acquire()
        frame = self.frame.copy()
        self.lock.release()
        if encode:
            _, buffer = imencode(".jpeg", frame)
            return base64.b64encode(buffer)
        return frame

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stream.release()

class Assistant:
    def __init__(self):
        self.chat_history = []

    async def answer(self, prompt, image):
        if not prompt:
            return
        print("Prompt:", prompt)

        # Prepare messages for Groq API
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self.chat_history,
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{image.decode()}"
                    }
                ]
            }
        ]

        # Call Groq API for Llama 4
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": LLAMA4_MODEL,
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7
        }

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: requests.post(GROQ_API_URL, headers=headers, json=payload)
            )
            response.raise_for_status()
            response_text = response.json()["choices"][0]["message"]["content"].strip()
            print("Response:", response_text)

            # Update chat history
            self.chat_history.append({"role": "user", "content": prompt})
            self.chat_history.append({"role": "assistant", "content": response_text})
            if len(self.chat_history) > 10:  # Limit history
                self.chat_history = self.chat_history[-10:]

            # Generate TTS
            if response_text:
                await self._tts(response_text)

        except requests.RequestException as e:
            print(f"Error calling Groq API: {e}")

    async def _tts(self, response):
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "playai-tts",
            "input": response,
            "voice": "alloy",
            "response_format": "pcm"
        }

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda

: requests.post(GROQ_TTS_URL, headers=headers, json=payload)
            )
            response.raise_for_status()
            audio_data = response.content

            # Play audio
            player = pyaudio.PyAudio()
            stream = player.open(format=FORMAT, channels=CHANNELS, rate=24000, output=True)
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            player.terminate()

        except requests.RequestException as e:
            print(f"Error generating TTS: {e}")

async def capture_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("Listening...")
    frames = []
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    return b''.join(frames)

async def transcribe_audio(audio_data):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "multipart/form-data"
    }
    files = {
        "file": ("audio.wav", audio_data, "audio/wav"),
        "model": (None, "distil-whisper-large-v3"),
        "response_format": (None, "json")
    }

    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: requests.post(GROQ_STT_URL, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, files=files)
        )
        response.raise_for_status()
        return response.json().get("text", "")
    except requests.RequestException as e:
        print(f"Error transcribing audio: {e}")
        return ""

async def main():
    webcam_stream = WebcamStream().start()
    assistant = Assistant()

    while True:
        # Capture and transcribe audio
        audio_data = await capture_audio()
        prompt = await transcribe_audio(audio_data)
        
        if prompt:
            image = webcam_stream.read(encode=True)
            await assistant.answer(prompt, image)
        
        # Display webcam feed
        cv2.imshow("webcam", webcam_stream.read())
        if cv2.waitKey(1) in [27, ord("q")]:
            break

    webcam_stream.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(main())