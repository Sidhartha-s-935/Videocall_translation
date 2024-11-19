import torch
from transformers import pipeline
import sounddevice as sd
import numpy as np
import queue
import threading
import time

# Configuration
device = "cuda:0" if torch.cuda.is_available() else "cpu"
model_id = "openai/whisper-small"

# Load model and pipeline
pipe = pipeline(
    "automatic-speech-recognition",
    model=model_id,
    device=0 if torch.cuda.is_available() else -1,
)

class RealtimeTranscriber:
    def __init__(self, sample_rate=16000, channels=1, chunk_duration=1.0):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        
    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Audio input status: {status}")
        
        # Convert to mono if stereo
        if indata.ndim > 1:
            indata = indata.mean(axis=1)
        
        self.audio_queue.put(indata.copy())
    
    def transcribe_chunk(self, audio_chunk):
        try:
            # Convert numpy array to float32 and normalize
            audio_float = audio_chunk.astype(np.float32) / np.max(np.abs(audio_chunk))
            
            # Transcribe the audio chunk
            result = pipe(audio_float)
            
            # Print transcription if text is not empty
            if result and result.get('text', '').strip():
                print("Transcription:", result['text'])
        except Exception as e:
            print(f"Transcription error: {e}")
    
    def process_audio(self):
        audio_buffer = []
        while not self.stop_event.is_set():
            try:
                # Get audio chunk with a timeout to allow checking stop event
                audio_chunk = self.audio_queue.get(timeout=0.1)
                audio_buffer.append(audio_chunk)
                
                # When buffer reaches chunk size, process and clear
                if len(np.concatenate(audio_buffer)) >= self.chunk_size:
                    full_chunk = np.concatenate(audio_buffer)
                    self.transcribe_chunk(full_chunk)
                    audio_buffer.clear()
            
            except queue.Empty:
                # Normal timeout, just continue
                continue
            except Exception as e:
                print(f"Audio processing error: {e}")
    
    def start_transcription(self):
        # Start audio input stream
        try:
            # Start processing thread
            process_thread = threading.Thread(target=self.process_audio, daemon=True)
            process_thread.start()
            
            # Start audio input stream
            with sd.InputStream(
                callback=self.audio_callback, 
                channels=self.channels, 
                samplerate=self.sample_rate
            ):
                print("Listening... Press Ctrl+C to stop.")
                
                # Keep main thread alive
                while not self.stop_event.is_set():
                    time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\nStopping transcription...")
        
        finally:
            # Set stop event to exit processing thread
            self.stop_event.set()

def main():
    transcriber = RealtimeTranscriber()
    transcriber.start_transcription()

if __name__ == "__main__":
    main()
