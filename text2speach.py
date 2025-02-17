import gtts
import os
import pygame
import time

def speak_input(input_text):
    """
    Convert input text to speech in English (en-US).
    
    :param input_text: Text to be spoken
    """
    lang_code = "en-US"  # Fixed to English

    try:
        # Generate speech audio
        audio_file = f"output_{lang_code}.mp3"
        tts = gtts.gTTS(text=input_text, lang=lang_code.split('-')[0])
        tts.save(audio_file)

        # Initialize pygame mixer
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()

        # Wait until playback finishes
        while pygame.mixer.music.get_busy():
            time.sleep(0.5)

        # Stop and unload the file before deleting
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        time.sleep(0.5)  # Ensure pygame releases the file

        # Remove temporary file
        os.remove(audio_file)

    except Exception as e:
        print(f"Error speaking in English: {e}")

    return input_text