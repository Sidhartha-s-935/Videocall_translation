from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from model import ContinuousTranscriber
import threading
import multiprocessing
from caption_window import run_caption_window
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    transport='websocket'
)

transcriber = None
connected_clients = set()

@socketio.on('connect')
def handle_connect():
    connected_clients.add(request.sid)
    logger.info(f"Client connected. SID: {request.sid}. Total clients: {len(connected_clients)}")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_clients:
        connected_clients.remove(request.sid)
    logger.info(f"Client disconnected. SID: {request.sid}. Total clients: {len(connected_clients)}")

def transcription_callback(transcription, translation):
    try:
        if not connected_clients:
            logger.warning("No connected clients to broadcast to")
            return

        data = {
            'transcription': transcription,
            'translation': translation
        }
        
        logger.info(f"Emitting to {len(connected_clients)} clients: {data}")
        
        # Remove the broadcast parameter and emit directly
        socketio.emit('transcription_update', data)
        
        logger.info("Emission completed successfully")
        
    except Exception as e:
        logger.error(f"Error in transcription callback: {e}", exc_info=True)

@app.route('/')
def index():
    temp_transcriber = ContinuousTranscriber()
    languages = temp_transcriber.available_languages
    return render_template('index.html', languages=languages)

@app.route('/start_transcription', methods=['POST'])
def start_transcription():
    global transcriber

    try:
        data = request.json
        target_lang = data.get('target_lang', 'en')

        if transcriber:
            transcriber.stop_transcription()

        transcriber = ContinuousTranscriber(target_language=target_lang)
        transcriber.set_callback(transcription_callback)

        thread = threading.Thread(target=transcriber.start_transcription, daemon=True)
        thread.start()

        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error starting transcription: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/stop_transcription', methods=['POST'])
def stop_transcription():
    global transcriber
    try:
        if transcriber:
            transcriber.stop_transcription()
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error stopping transcription: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)})

def run_server():
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False)

if __name__ == '__main__':
    # Start the caption window in a separate process
    caption_process = multiprocessing.Process(target=run_caption_window)
    caption_process.start()

    # Run the server
    try:
        run_server()
    finally:
        caption_process.terminate()
        caption_process.join()
