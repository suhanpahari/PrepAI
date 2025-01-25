import whisper


model = whisper.load_model("base")  

audio_file = "indian_english_audio.wav"

result = model.transcribe(audio_file)

print("Transcription:")
print(result["text"])

with open("transcription.txt", "w") as f:
    f.write(result["text"])

print("Transcription saved to 'transcription.txt'")