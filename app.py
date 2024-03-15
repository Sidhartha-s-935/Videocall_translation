import subprocess
import os
import json
from flask import Flask, render_template, request, jsonify
from googletrans import Translator
from whisper_translator import WhisperTranslator  

app = Flask(__name__)

# Initialize translators
google_translator = Translator()
whisper_translator = WhisperTranslator()

subprocess.Popen(["python", "desktop_app.py"])

CACHE_FILE_PATH = 'translation_cache.json'
translation_cache = {}

def load_cache():
    if os.path.exists(CACHE_FILE_PATH):
        with open(CACHE_FILE_PATH, 'r') as file:
            return json.load(file)
    return {}

def save_cache():
    with open(CACHE_FILE_PATH, 'w') as file:
        json.dump(translation_cache, file)

def update_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(content + '\n')

def get_translation_from_cache(text, source_language, target_language):
    key = f"{text}_{source_language}_{target_language}"
    return translation_cache.get(key)

def add_translation_to_cache(text, source_language, target_language, translation):
    update_file("transcript.txt", text)
    update_file("translated.txt", translation)
    key = f"{text}_{source_language}_{target_language}"
    translation_cache[key] = translation
    save_cache()

@app.before_request
def before_first_request():
    if not hasattr(app, 'has_run_before_first_request'):
        load_cache_on_startup()
        app.has_run_before_first_request = True

def load_cache_on_startup():
    global translation_cache
    translation_cache = load_cache()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate-text', methods=['POST'])
def translate_text():
    try:
        data = request.get_json()
        text = data['text']
        target_language = data['target_language']
        source_language = data['source_language']

        # Use selected translation model
        if data.get('translation_model') == 'whisper':
            translation = whisper_translator.translate(text, source_language, target_language)
        else:
            translation = google_translator.translate(text, dest=target_language, src=source_language).text

        add_translation_to_cache(text, source_language, target_language, translation)

        return jsonify({'translation': translation})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
