import os
import json
import sqlite3
from flask import Flask, render_template, request, jsonify
from googletrans import Translator
import subprocess

subprocess.Popen(["python", "desktop_app.py"])

app = Flask(__name__)

google_translator = Translator()

DATABASE_FILE_PATH = 'translation_cache.db'
TRANSLATED_FILE_PATH = 'translated.txt'

CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    source_language TEXT,
    target_language TEXT,
    translation TEXT
)
'''

def get_database_connection():
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    conn.execute(CREATE_TABLE_SQL)  
    conn.commit()
    return conn

def add_translation_to_database(text, source_language, target_language, translation):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO translations (text, source_language, target_language, translation) VALUES (?, ?, ?, ?)',
                   (text, source_language, target_language, translation))
    conn.commit()
    conn.close()
    update_translated_file(translation)

def update_translated_file(translation):
    with open(TRANSLATED_FILE_PATH, 'w', encoding='utf-8') as file:
        file.write(translation + '\n')

def get_translation_from_database(text, source_language, target_language):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT translation FROM translations WHERE text = ? AND source_language = ? AND target_language = ?',
                   (text, source_language, target_language))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

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
        
        translation = get_translation_from_database(text, source_language, target_language)

        if translation is None:
            translation = google_translator.translate(text, dest=target_language, src=source_language).text
            add_translation_to_database(text, source_language, target_language, translation)

        return jsonify({'translation': translation})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
