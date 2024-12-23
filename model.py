import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, AutoModelForSeq2SeqLM, AutoTokenizer
import sounddevice as sd
import numpy as np
import queue
import threading
import time
import difflib

# Configuration
device = "cuda:0" if torch.cuda.is_available() else "cpu"
transcription_model = "openai/whisper-small"

# Translation models for Indian languages
translation_models = {
    'hi': 'Helsinki-NLP/opus-mt-en-hi',
    'ta': 'Helsinki-NLP/opus-mt-en-ta',
    'te': 'Helsinki-NLP/opus-mt-en-te',
    'bn': 'Helsinki-NLP/opus-mt-en-bn'
}

class ContinuousTranscriber:
    def __init__(self, sample_rate=16000, channels=1, target_language='en'):
        self.sample_rate = sample_rate
        self.channels = channels
        self.target_language = target_language
        
        # Audio collection parameters
        self.audio_buffer = []
        self.max_buffer_size = sample_rate * 2  # 5-second buffer
        
        # Load transcription model and processor
        self.transcribe_model = AutoModelForSpeechSeq2Seq.from_pretrained(transcription_model).to(device)
        self.processor = AutoProcessor.from_pretrained(transcription_model)
        
        # Initialize translation model if needed
        self.translate_model = None
        self.translate_tokenizer = None
        if target_language != 'en':
            model_name = translation_models.get(target_language)
            if model_name:
                self.translate_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.translate_model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
        
        # Transcription tracking
        self.last_full_transcription = ""
        self.transcription_threshold = 0.8  # Similarity threshold
    
    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Audio input status: {status}")
        
        # Convert to mono if stereo
        audio_chunk = indata.mean(axis=1) if indata.ndim > 1 else indata
        
        # Add to audio buffer
        self.audio_buffer.extend(audio_chunk)
        
        # Trim buffer if it gets too long
        if len(self.audio_buffer) > self.max_buffer_size:
            self.audio_buffer = self.audio_buffer[-self.max_buffer_size:]
    
    def compute_similarity(self, seq1, seq2):
        """Compute similarity between two sequences."""
        return difflib.SequenceMatcher(None, seq1, seq2).ratio()
    
    def transcribe_and_translate(self):
        try:
            # Convert buffer to numpy array and normalize
            audio_data = np.array(self.audio_buffer[-self.sample_rate * 2:]).astype(np.float32)
            audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Prepare input for transcription model
            inputs = self.processor(audio_data, sampling_rate=self.sample_rate, return_tensors="pt").to(device)
            
            # Transcribe
            with torch.no_grad():
                output_ids = self.transcribe_model.generate(inputs.input_features)
                transcription = self.processor.batch_decode(output_ids, skip_special_tokens=True)[0]
            
            transcription = transcription.strip()
            
            # Check if transcription is significantly different from last one
            if transcription and (
                not self.last_full_transcription or 
                self.compute_similarity(transcription, self.last_full_transcription) < self.transcription_threshold
            ):
                print("Transcription:", transcription)
                self.last_full_transcription = transcription
                
                # Translate if target language is not English
                if self.target_language != 'en' and self.translate_model and self.translate_tokenizer:
                    translate_inputs = self.translate_tokenizer(
                        transcription, 
                        return_tensors="pt", 
                        padding=True
                    ).to(device)
                    
                    with torch.no_grad():
                        outputs = self.translate_model.generate(**translate_inputs)
                        translated_text = self.translate_tokenizer.decode(outputs[0], skip_special_tokens=True)
                    
                    print(f"Translation ({self.target_language}):", translated_text)
        
        except Exception as e:
            print(f"Transcription/Translation error: {e}")
    
    def start_transcription(self):
        try:
            # Start audio input stream
            with sd.InputStream(
                callback=self.audio_callback, 
                channels=self.channels, 
                samplerate=self.sample_rate
            ):
                print("Listening... Press Ctrl+C to stop.")
                
                # Continuously transcribe and translate
                while True:
                    # Wait a bit before next transcription attempt
                    time.sleep(1)
                    
                    # Only transcribe if we have enough audio
                    if len(self.audio_buffer) > self.sample_rate:
                        self.transcribe_and_translate()
        
        except KeyboardInterrupt:
            print("\nStopping transcription...")

def main():
    print("Select Target Language:")
    print("1. English")
    print("2. Hindi")
    print("3. Tamil")
    print("4. Telugu")
    print("5. Bengali")
    
    language_map = {
        '1': 'en',
        '2': 'hi',
        '3': 'ta',
        '4': 'te',
        '5': 'bn'
    }
    
    choice = input("Enter the number of your desired language: ")
    target_language = language_map.get(choice, 'en')
    
    transcriber = ContinuousTranscriber(target_language=target_language)
    transcriber.start_transcription()

if __name__ == "__main__":
    main()

