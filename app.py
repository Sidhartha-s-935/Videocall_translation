from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from model import ContinuousTranscriber
import threading
import multiprocessing
from caption_window import run_caption_window

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

transcriber = None

@app.route('/')
def index():
    # Use the languages from the ContinuousTranscriber class
    temp_transcriber = ContinuousTranscriber()
    languages = temp_transcriber.available_languages
    return render_template('index.html', languages=languages)

def transcription_callback(transcription, translation):
    socketio.emit('transcription_update', {
        'transcription': transcription,
        'translation': translation
    })

@app.route('/start_transcription', methods=['POST'])
def start_transcription():
    global transcriber
    
    data = request.json
    target_lang = data.get('target_lang', 'en')
    
    if transcriber:
        transcriber.stop_transcription()
    
    transcriber = ContinuousTranscriber(target_language=target_lang)
    transcriber.set_callback(transcription_callback)
    
    thread = threading.Thread(target=transcriber.start_transcription, daemon=True)
    thread.start()
    
    return jsonify({'status': 'success'})

@app.route('/stop_transcription', methods=['POST'])
def stop_transcription():
    global transcriber
    if transcriber:
        transcriber.stop_transcription()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    caption_process = multiprocessing.Process(target=run_caption_window)
    caption_process.start()
    socketio.run(app, debug=True)
