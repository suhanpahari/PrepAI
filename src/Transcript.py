import whisper
import sounddevice as sd
import numpy as np
import wave

# Load the Whisper model
model = whisper.load_model("base")

def record_audio(filename, duration=35, samplerate=16000):
    print("Speak now...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
    sd.wait()
    
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(recording.tobytes())

def transcribe_audio(filename):
    result = model.transcribe(filename)
    return result["text"].strip()

if __name__ == "__main__":
    audio_file = "test_audio.wav"
    record_audio(audio_file, duration=5)  # Record for 5 seconds
    transcription = transcribe_audio(audio_file)
    print("Transcription:", transcription)
