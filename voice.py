import asyncio
import base64
import cv2
import os
import pyaudio
import requests
import wave
import io
import time
from threading import Lock, Thread
from cv2 import VideoCapture, imencode
from dotenv import load_dotenv

# Whisper will be imported when needed to avoid loading the model at startup

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
        self.stream = VideoCapture(0)
        success, self.frame = self.stream.read()
        if not success:
            raise RuntimeError("Could not initialize webcam")
        self.running = False
        self.lock = Lock()

    def start(self):
        if self.running:
            return self
        self.running = True
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True  # Make thread daemon so it exits when main program exits
        self.thread.start()
        return self

    def update(self):
        while self.running:
            success, frame = self.stream.read()
            if success:
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
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.stream.release()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

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
            
            return response_text

        except requests.RequestException as e:
            print(f"Error calling Groq API: {e}")
            return f"Error: {str(e)}"

    async def _tts(self, response):
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "playai-tts",
            "input": response,
            "voice": "alloy",
            "response_format": "mp3"  # Changed from pcm to mp3 for better compatibility
        }

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: requests.post(GROQ_TTS_URL, headers=headers, json=payload)
            )
            response.raise_for_status()
            audio_data = response.content

            # Play audio using system audio players
            # This requires proper handling of mp3 data
            player = pyaudio.PyAudio()
            
            # For mp3 files, you might need an external library like pydub
            # Here we'll assume you've converted to a playable format
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
    
    # Convert to WAV format for API compatibility
    audio_data = io.BytesIO()
    with wave.open(audio_data, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    
    return audio_data.getvalue()

async def transcribe_audio(audio_data):
    try:
        # Save audio data to a temporary WAV file
        temp_file = "temp_audio.wav"
        with open(temp_file, "wb") as f:
            f.write(audio_data)
        
        # Use local Whisper model via a worker thread
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: transcribe_with_local_whisper(temp_file)
        )
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""

def transcribe_with_local_whisper(audio_file):
    """Transcribe audio using locally installed Whisper model"""
    import whisper  # Import here to avoid loading the model until needed
    
    print("Transcribing with local Whisper model...")
    # Load the medium model
    model = whisper.load_model("medium")
    
    # Transcribe the audio
    result = model.transcribe(audio_file)
    
    # Clean up temp file
    try:
        os.remove(audio_file)
    except:
        pass
        
    return result["text"]

async def main():
    try:
        webcam_stream = WebcamStream().start()
        assistant = Assistant()
        
        print("Assistant started. Press 'q' or ESC to exit.")
        print("Loading local Whisper model (this may take a moment)...")
        
        # Pre-load the Whisper model to avoid delay during first transcription
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: preload_whisper_model()
        )
        
        while True:
            # Display webcam feed with status
            frame = webcam_stream.read()
            cv2.putText(frame, "Listening...", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Webcam Assistant", frame)
            
            # Check for exit
            key = cv2.waitKey(1)
            if key in [27, ord("q")]:
                break
                
            # Capture and transcribe audio
            audio_data = await capture_audio()
            
            # Show processing status
            frame = webcam_stream.read()
            cv2.putText(frame, "Processing speech...", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Webcam Assistant", frame)
            cv2.waitKey(1)
            
            prompt = await transcribe_audio(audio_data)
            
            if prompt.strip():
                # Display transcribed text
                frame = webcam_stream.read()
                # Truncate long text for display
                display_text = prompt[:50] + "..." if len(prompt) > 50 else prompt
                cv2.putText(frame, f"You: {display_text}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Webcam Assistant", frame)
                cv2.waitKey(1)
                
                # Show thinking status
                frame = webcam_stream.read()
                cv2.putText(frame, f"You: {display_text}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, "Thinking...", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.imshow("Webcam Assistant", frame)
                cv2.waitKey(1)
                
                # Get response
                image = webcam_stream.read(encode=True)
                response = await assistant.answer(prompt, image)
                
                # Display response
                if response:
                    frame = webcam_stream.read()
                    display_response = response[:50] + "..." if len(response) > 50 else response
                    cv2.putText(frame, f"You: {display_text}", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"Assistant: {display_response}", (10, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    cv2.imshow("Webcam Assistant", frame)
            
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        if 'webcam_stream' in locals():
            webcam_stream.stop()
        cv2.destroyAllWindows()
        
def preload_whisper_model():
    """Pre-load the Whisper model to avoid delay during first transcription"""
    import whisper
    print("Loading Whisper medium model...")
    _ = whisper.load_model("medium")
    print("Whisper model loaded and ready!")

if __name__ == "__main__":
    asyncio.run(main())