from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
from model import ContinuousTranscriber

# Flask Application
app = Flask(__name__)
socketio = SocketIO(app)

# Supported languages
LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'ta': 'Tamil', 
    'te': 'Telugu',
    'bn': 'Bengali',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'ru': 'Russian'
}

# Global transcriber variable
transcriber = None

@app.route('/')
def index():
    return render_template('index.html', languages=LANGUAGES)

@socketio.on('start_transcription')
def handle_start_transcription(data):
    global transcriber
    
    def socket_callback(transcription_data):
        # Emit transcription via SocketIO
        socketio.emit('transcription_update', transcription_data)
    
    # Get source language (optional)
    source_language = data.get('source_language', 'en')
    
    # Get target translation languages
    target_languages = data.get('target_languages', [])
    
    # If no target languages specified, just transcribe
    if not target_languages:
        target_languages = ['en']
    
    # Stop any existing transcription
    if transcriber:
        # Implement a stop method in your model if needed
        del transcriber
    
    # Create transcriber for each target language
    transcribers = []
    for target_lang in target_languages:
        trans = ContinuousTranscriber(
            callback_fn=socket_callback, 
            target_language=target_lang,
            source_language=source_language
        )
        transcribers.append(trans)
        # Start each transcriber in a separate thread
        threading.Thread(target=trans.start_transcription, daemon=True).start()

def main():
    socketio.run(app, debug=True, host='0.0.0.0')

if __name__ == '__main__':
    main()
