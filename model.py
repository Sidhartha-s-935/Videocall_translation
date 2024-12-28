import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, MarianMTModel, MarianTokenizer
import sounddevice as sd
import numpy as np
import threading
import queue
import time
import logging
import traceback

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ContinuousTranscriber:
    def __init__(self, target_language='en'):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        logging.info(f"Using device: {self.device}")
        
        self.sample_rate = 16000
        self.buffer = queue.Queue()
        self.running = False
        self.buffer_duration = 2  # seconds
        self.samples_per_chunk = int(self.sample_rate * self.buffer_duration)
        self.callback_function = None
        self.min_audio_level = 0.01
        
        # Language mapping for ROMANCE model
        # These are the languages supported by the ROMANCE model
        self.available_languages = {
            'English': 'en',
            'Spanish': 'es',
            'French': 'fr',
            'Italian': 'it',
            'Portuguese': 'pt',
            'Romanian': 'ro',
            'Catalan': 'ca'
        }
        
        # Language codes for the ROMANCE model
        self.romance_language_codes = {
            'es': 'es_ES',
            'fr': 'fr_FR',
            'it': 'it_IT',
            'pt': 'pt_PT',
            'ro': 'ro_RO',
            'ca': 'ca_ES'
        }
        
        # Validate and set target language
        self.target_language = self._validate_language(target_language)
        logging.info(f"Target language set to: {self.target_language}")
        
        # Initialize Whisper model for transcription
        logging.info("Loading Whisper model...")
        self.model_id = "openai/whisper-small"
        
        self.dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        logging.info(f"Using dtype: {self.dtype}")
        
        try:
            self.whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_id,
                torch_dtype=self.dtype,
                device_map="auto",
                use_safetensors=True
            )
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            logging.info("Whisper model loaded successfully")
        except Exception as e:
            logging.error(f"Error loading Whisper model: {str(e)}")
            raise

        # Initialize Helsinki-NLP ROMANCE translation model
        if self.target_language != 'en':
            try:
                self.translation_model_name = "Helsinki-NLP/opus-mt-en-ROMANCE"
                logging.info(f"Loading translation model: {self.translation_model_name}")
                self.translation_model = MarianMTModel.from_pretrained(
                    self.translation_model_name
                ).to(self.device)
                self.translation_tokenizer = MarianTokenizer.from_pretrained(
                    self.translation_model_name
                )
                logging.info("Translation model loaded successfully")
            except Exception as e:
                logging.error(f"Error loading translation model: {str(e)}")
                self.translation_model = None
                self.translation_tokenizer = None

        self.processing_thread = None
        self.stream = None

    def _validate_language(self, language_code):
        """Validate language code and return normalized version"""
        # First check if it's a valid language code
        if language_code in self.available_languages.values():
            return language_code
        
        # Then check if it's a valid language name
        for name, code in self.available_languages.items():
            if language_code.lower() == name.lower():
                return code
        
        logging.warning(f"Invalid language code '{language_code}', defaulting to English")
        return 'en'

    def _get_language_name(self, language_code):
        """Get full language name from code"""
        try:
            return next(name for name, code in self.available_languages.items()
                       if code == language_code)
        except StopIteration:
            return language_code

    def _translate_text(self, text):
        """Translate text using Helsinki-NLP ROMANCE model"""
        if not text or self.target_language == 'en' or not self.translation_model:
            return None
            
        try:
            # Get the appropriate target language code for the ROMANCE model
            target_lang_code = self.romance_language_codes.get(self.target_language)
            if not target_lang_code:
                logging.error(f"Unsupported target language: {self.target_language}")
                return None

            # Prepare the input text with the target language code
            input_text = f">>{target_lang_code}<< {text}"
            
            # Tokenize and translate
            inputs = self.translation_tokenizer(
                input_text, 
                return_tensors="pt", 
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                translated_ids = self.translation_model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=4,
                    length_penalty=0.6,
                    early_stopping=True
                )
            
            # Decode translation
            translation = self.translation_tokenizer.decode(
                translated_ids[0], 
                skip_special_tokens=True
            )
            return translation
            
        except Exception as e:
            logging.error(f"Translation error: {str(e)}")
            return None

    def process_audio_chunk(self, audio_data):
        try:
            # Check audio level
            audio_level = np.max(np.abs(audio_data))
            if audio_level < self.min_audio_level:
                logging.debug(f"Audio level too low: {audio_level}")
                return None, None
            
            # Normalize audio
            audio_data = audio_data / audio_level
            
            # Create input features
            inputs = self.processor(
                audio_data, 
                sampling_rate=self.sample_rate, 
                return_tensors="pt"
            )
            
            # Move to device and set dtype
            input_features = inputs.input_features.to(self.device).to(self.dtype)
            
            # Create attention mask
            attention_mask = torch.ones(
                input_features.shape[:2],
                dtype=torch.long,
                device=self.device
            )
            
            # Transcribe
            with torch.no_grad():
                logging.debug("Starting transcription generation")
                generated_ids = self.whisper_model.generate(
                    input_features,
                    attention_mask=attention_mask,
                    language="en",
                    task="transcribe",
                    max_length=448,
                    no_repeat_ngram_size=3,
                    num_beams=2
                )
                
                transcription = self.processor.batch_decode(
                    generated_ids, 
                    skip_special_tokens=True
                )[0].strip()
                
                if not transcription:
                    logging.debug("No transcription generated")
                    return None, None
                
                # Translate using ROMANCE model
                translation = self._translate_text(transcription)
            
            return transcription, translation
            
        except Exception as e:
            logging.error(f"Error processing audio chunk: {str(e)}")
            logging.error(traceback.format_exc())
            return None, None

    def set_callback(self, callback):
        self.callback_function = callback
        logging.info("Callback function set")
    
    def audio_callback(self, indata, frames, time_info, status):
        if status:
            logging.warning(f"Audio status: {status}")
        
        try:
            audio_data = indata.mean(axis=1) if indata.ndim > 1 else indata.flatten()
            self.buffer.put(audio_data.copy())
        except Exception as e:
            logging.error(f"Error in audio callback: {str(e)}")
    
    def process_audio(self):
        logging.info("Starting audio processing loop")
        while self.running:
            try:
                # Collect audio chunks
                audio_chunks = []
                current_size = 0
                start_time = time.time()
                
                while current_size < self.samples_per_chunk and self.running:
                    try:
                        chunk = self.buffer.get(timeout=0.1)
                        audio_chunks.append(chunk)
                        current_size += len(chunk)
                        
                        if time.time() - start_time > self.buffer_duration * 1.5:
                            logging.warning("Buffer collection timeout")
                            break
                            
                    except queue.Empty:
                        continue
                
                if not self.running:
                    break
                    
                if not audio_chunks:
                    continue
                
                audio_data = np.concatenate(audio_chunks)
                if len(audio_data) > self.samples_per_chunk:
                    audio_data = audio_data[:self.samples_per_chunk]
                
                transcription, translation = self.process_audio_chunk(audio_data)
                
                if transcription and self.callback_function:
                    self.callback_function(transcription, translation)
                    
                    lang_name = self._get_language_name(self.target_language)
                    logging.info(f"English: {transcription}")
                    if translation:
                        logging.info(f"Translation ({lang_name}): {translation}")
                
            except Exception as e:
                logging.error(f"Error in audio processing loop: {str(e)}")
                logging.error(traceback.format_exc())
                time.sleep(0.1)
    
    def start_transcription(self):
        if self.running:
            logging.warning("Transcription already running")
            return
        
        self.running = True
        logging.info("Starting transcription")
        
        try:
            self.stream = sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=int(self.sample_rate * 0.1)
            )
            self.stream.start()
            logging.info("Audio stream started")
            
            self.processing_thread = threading.Thread(target=self.process_audio)
            self.processing_thread.start()
            logging.info("Processing thread started")
            
        except Exception as e:
            self.running = False
            logging.error(f"Error starting transcription: {str(e)}")
            logging.error(traceback.format_exc())
            raise
    
    def stop_transcription(self):
        logging.info("Stopping transcription")
        self.running = False
        
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
                logging.info("Audio stream stopped")
            
            if self.processing_thread:
                self.processing_thread.join(timeout=2.0)
                if self.processing_thread.is_alive():
                    logging.warning("Processing thread did not stop cleanly")
                self.processing_thread = None
            
            while not self.buffer.empty():
                try:
                    self.buffer.get_nowait()
                except queue.Empty:
                    break
            
            logging.info("Transcription stopped successfully")
            
        except Exception as e:
            logging.error(f"Error stopping transcription: {str(e)}")
            logging.error(traceback.format_exc())
