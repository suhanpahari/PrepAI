import pyaudio
import webrtcvad
import numpy as np
import wave
import tempfile
import os
import asyncio
import logging
import struct
from groq import Groq
from elevenlabs.client import AsyncElevenLabs
from pygame import mixer
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API keys from environment variables with fallback to hardcoded values
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_a02661bc72a15d32268f049f94708c0b76433c20b0f2e403")

# Initialize clients
groq_client = Groq(api_key=GROQ_API_KEY)
elevenlabs_client = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)

class VoiceDetector:
    def __init__(self, sample_rate=16000, frame_duration_ms=30, min_speech_frames=10, max_silence_frames=50):
        self.vad = webrtcvad.Vad(3)  # Aggressive VAD mode
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
            temp_wav_name = temp_wav.name  # Save name before closing
            with wave.open(temp_wav_name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data)

        # File is now fully written and closed
        with open(temp_wav_name, 'rb') as audio_file:
            response = groq_client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                response_format="text"
            )

        os.unlink(temp_wav_name)
        return response
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return None

async def generate_response(text: str):
    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful voice assistant. Provide concise responses (max 2 sentences)."},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=100
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Chat response error: {str(e)}")
        return "I'm sorry, I couldn't process your request."  # Fallback response that will be spoken

async def generate_speech(text: str):
    try:
        # Using async generator to fetch chunks of audio
        audio_data = b""
        async_response = elevenlabs_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",  # Alloy voice
            text=text,
            model_id="eleven_monolingual_v1"
        )
        
        # Properly iterate through the async generator
        async for chunk in async_response:
            audio_data += chunk  # Collect the audio data in chunks

        return audio_data
    except Exception as e:
        logger.error(f"Speech generation error: {str(e)}")
        # Generate a local fallback response if ElevenLabs fails
        return await generate_fallback_audio("I'm sorry, I'm having trouble generating speech right now.")
    
async def generate_fallback_audio(text: str):
    # Simple fallback if ElevenLabs fails - requires pyttsx3 library
    # This is a placeholder - you may need to implement a different fallback method
    try:
        import pyttsx3
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            engine = pyttsx3.init()
            engine.save_to_file(text, temp_file.name)
            engine.runAndWait()
            with open(temp_file.name, 'rb') as f:
                return f.read()
    except ImportError:
        logger.error("pyttsx3 not installed for fallback audio")
        return None
    except Exception as e:
        logger.error(f"Fallback audio generation error: {str(e)}")
        return None

async def play_audio(audio_data: bytes):
    if not audio_data:
        logger.error("No audio data to play")
        return
        
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
            temp_mp3.write(audio_data)
            temp_mp3.flush()
            temp_mp3_name = temp_mp3.name
            
        # Initialize outside the with block to ensure the file is closed
        mixer.init()
        mixer.music.load(temp_mp3_name)
        mixer.music.play()
        
        print("\nSpeaking...", end="")
        
        while mixer.music.get_busy():
            await asyncio.sleep(0.1)
            
        mixer.quit()
        os.unlink(temp_mp3_name)
        print(" Done.")
    except Exception as e:
        logger.error(f"Audio playback error: {str(e)}")

async def speak_startup_message():
    """Generate and play a startup message to confirm the system is working."""
    startup_message = "Voice assistant is now active. I'm listening for your commands."
    print("Generating startup voice message...")
    audio_data = await generate_speech(startup_message)
    if audio_data:
        await play_audio(audio_data)
    else:
        print("Failed to generate startup voice message")

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

    print("Voice Assistant started. Speak to interact, silence to get a response. Interrupt by speaking.")
    print("Press Ctrl+C to exit.")
    
    # Play startup message
    await speak_startup_message()

    try:
        while True:
            data = stream.read(1024, exception_on_overflow=False)
            voice_detected = voice_detector.detect_voice(data)

            print(f"\r{'Listening...' if voice_detected else 'Waiting for speech...'}", end="")

            if voice_detected:
                audio_buffer.extend(data)
                if is_responding:
                    is_responding = False
                    mixer.music.stop()
                    print("\nResponse interrupted.")
            else:
                if len(audio_buffer) > 0 and voice_detector.silence_frames >= voice_detector.max_silence_frames and not is_responding:
                    print("\nProcessing audio...")
                    transcription = await transcribe_audio(bytes(audio_buffer))
                    audio_buffer.clear()
                    
                    if transcription:
                        print(f"Transcription: {transcription}")
                        response_text = await generate_response(transcription)
                        
                        if response_text:
                            print(f"Response: {response_text}")
                            is_responding = True
                            
                            # Always generate and play speech response
                            speech_audio = await generate_speech(response_text)
                            if speech_audio:
                                await play_audio(speech_audio)
                            else:
                                print("Error: Failed to generate speech")
                                
                            is_responding = False
                    else:
                        # Provide audio feedback for failed transcription
                        error_message = "I couldn't understand what you said. Please try again."
                        print(error_message)
                        is_responding = True
                        error_audio = await generate_speech(error_message)
                        if error_audio:
                            await play_audio(error_audio)
                        is_responding = False
    except KeyboardInterrupt:
        print("\nExiting...")
        # Optional: add goodbye message
        goodbye_audio = await generate_speech("Voice assistant shutting down. Goodbye!")
        if goodbye_audio:
            await play_audio(goodbye_audio)
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        if pa:
            pa.terminate()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLI Voice Assistant using Groq and ElevenLabs")
    args = parser.parse_args()
    asyncio.run(main())