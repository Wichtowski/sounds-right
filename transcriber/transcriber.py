import json
import os
import whisper

class Transcriber:
    def __init__(self, model: whisper.model, lyrics=None):
        self.model = model
        self.lyrics = lyrics
        self.cache_dir = os.path.join(os.getcwd(), "cache")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    @staticmethod
    def clean_text(text):
        return text.replace('\n', ' ').strip()  

    @staticmethod
    def get_versioned_filename(filename):
        base_name, ext = os.path.splitext(filename)
        version = 1
        while os.path.exists(f"{base_name}_{version}{ext}"):
            version += 1
        return f"{base_name}_{version}{ext}"

    @staticmethod
    def align_lyrics_with_timestamps(lyrics, segments):
        if not lyrics:
            return segments
            
        words = [word for line in lyrics.splitlines() for word in line.split()]
        aligned_segments, word_index = [], 0
        
        for segment in segments:
            new_words = []
            for word_data in segment.get("words", []):
                if word_index < len(words):
                    new_words.append({
                        "word": words[word_index],
                        "start": word_data["start"],
                        "end": word_data["end"]
                    })
                    word_index += 1
                else:
                    break
            
            aligned_segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": " ".join(w["word"] for w in new_words),
                "words": new_words
            })
        
        return aligned_segments

    def transcribe_audio(self, audio_file, lyrics=None):
        """
        Transcribe audio file and align with lyrics if provided.
        
        Args:
            audio_file: Path to the audio file
            lyrics: Optional lyrics text
        """
        print("Transcribing audio...")
        result = self.model.transcribe(audio_file, word_timestamps=True, fp16=False)
        print("Transcription complete.")
        
        transcript_data = {
            "audio_file": os.path.basename(audio_file),
            "segments": self.align_lyrics_with_timestamps(lyrics, result["segments"]),
            "provided_lyrics": lyrics is not None
        }
        
        return transcript_data

# if __name__ == "__main__":
#     audio_file = "Kendrick Lamar - squabble up (Official Audio).mp3"
#     with open(audio_file.replace('.mp3', '.txt'), "r", encoding="utf-8") as file:
#         provided_lyrics = file.read()
    
#     transcriber = Transcriber()
#     transcript = transcriber.transcribe_audio(audio_file, provided_lyrics, 
#                                               output_filename=audio_file.replace('.mp3', '_transcription.json'),
#                                               cache_filename=audio_file.replace('.mp3', '_transcription_cache.json'))
    
#     output_file = audio_file.replace('.mp3', '_karaoke_timing.json')
#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(transcript, f, indent=4)
