from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import sys
import eventlet
eventlet.monkey_patch()

from model import ContinuousTranscriber

# Flask Application
app = Flask(__name__)

# Explicitly set async mode to eventlet
socketio = SocketIO(app, async_mode='eventlet')

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

# Global transcriber variables
active_transcribers = {}

@app.route('/')
def index():
    return render_template('index.html', languages=LANGUAGES)

@socketio.on('start_transcription')
def handle_start_transcription(data):
    global active_transcribers
    
    def socket_callback(transcription_data):
        # Emit transcription via SocketIO
        socketio.emit('transcription_update', transcription_data)
    
    # Get source language (optional, default to English)
    source_language = data.get('source_language', 'en')
    
    # Get target translation languages
    target_languages = data.get('target_languages', ['en'])
    
    # Stop any existing transcriptions
    stop_all_transcriptions()
    
    # Create and start transcribers for each target language
    for target_lang in target_languages:
        try:
            # Create transcriber for each target language
            transcriber = ContinuousTranscriber(
                target_language=target_lang
            )
            
            # Start transcription in a separate thread
            transcription_thread = threading.Thread(
                target=transcribe_wrapper, 
                args=(transcriber, target_lang, socket_callback), 
                daemon=True
            )
            transcription_thread.start()
            
            # Store the transcriber and thread
            active_transcribers[target_lang] = {
                'transcriber': transcriber,
                'thread': transcription_thread
            }
        except Exception as e:
            socketio.emit('error', {'message': f'Error starting transcription for {target_lang}: {str(e)}'})

def transcribe_wrapper(transcriber, language, callback):
    """
    Wrapper to add callback functionality to the transcription process
    """
    try:
        # Override the print statements with callback
        def custom_print(text):
            callback({
                'language': language,
                'text': text,
                'timestamp': time.time()
            })
        
        # Temporarily replace print with custom callback
        import builtins
        original_print = builtins.print
        builtins.print = custom_print
        
        try:
            # Start transcription
            transcriber.start_transcription()
        finally:
            # Restore original print
            builtins.print = original_print
    except Exception as e:
        callback({
            'language': language,
            'error': str(e),
            'timestamp': time.time()
        })

@socketio.on('stop_transcription')
def handle_stop_transcription():
    """
    Stop all active transcriptions
    """
    stop_all_transcriptions()
    socketio.emit('transcription_stopped')

def stop_all_transcriptions():
    """
    Utility function to stop all active transcription threads
    """
    global active_transcribers
    for lang, data in list(active_transcribers.items()):
        try:
            # You might want to add a stop method to ContinuousTranscriber
            # This is a placeholder - modify based on your actual implementation
            del active_transcribers[lang]
        except Exception as e:
            print(f"Error stopping transcription for {lang}: {e}")

def main():
    # Use host='0.0.0.0' to make the server externally visible
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
