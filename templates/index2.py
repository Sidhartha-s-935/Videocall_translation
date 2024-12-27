<!DOCTYPE html>
<html>
<head>
    <title>Real-time Translation</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .caption-box {
            background-color: black;
            color: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            min-height: 50px;
            font-size: 16px;
        }
        
        .translation-box {
            background-color: black;
            color: yellow;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            min-height: 50px;
            font-size: 16px;
        }
        
        .control-panel {
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        
        select {
            padding: 8px;
            margin: 5px 0;
            width: 200px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        .button-group {
            margin-top: 15px;
        }
        
        button {
            padding: 10px 20px;
            margin-right: 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        
        .start-btn {
            background-color: #28a745;
            color: white;
        }
        
        .stop-btn {
            background-color: #dc3545;
            color: white;
        }
        
        button:hover {
            opacity: 0.9;
        }
        
        .status {
            margin-top: 10px;
            font-style: italic;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Real-time Translation</h1>
        
        <div class="control-panel">
            <div>
                <label for="target-lang">Target Language:</label>
                <select id="target-lang">
                    {% for code, name in languages.items() %}
                    <option value="{{ code }}">{{ name }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="button-group">
                <button class="start-btn" onclick="startTranscription()">Start Translation</button>
                <button class="stop-btn" onclick="stopTranscription()">Stop Translation</button>
            </div>
            
            <div class="status" id="status">Status: Ready</div>
        </div>
        
        <div id="transcription" class="caption-box">
            Transcription will appear here...
        </div>
        
        <div id="translation" class="translation-box">
            Translation will appear here...
        </div>
    </div>
    
    <script>
        const socket = io();
        const statusElement = document.getElementById('status');
        
        socket.on('connect', () => {
            statusElement.textContent = 'Status: Connected';
        });
        
        socket.on('disconnect', () => {
            statusElement.textContent = 'Status: Disconnected';
        });
        
        socket.on('transcription_update', function(data) {
            document.getElementById('transcription').textContent = data.transcription || 'No transcription available';
            document.getElementById('translation').textContent = data.translation || 'No translation available';
        });
        
        function startTranscription() {
            const targetLang = document.getElementById('target-lang').value;
            statusElement.textContent = 'Status: Starting translation...';
            
            fetch('/start_transcription', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    target_lang: targetLang
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    statusElement.textContent = 'Status: Translation active';
                }
            });
        }
        
        function stopTranscription() {
            statusElement.textContent = 'Status: Stopping translation...';
            
            fetch('/stop_transcription', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    statusElement.textContent = 'Status: Ready';
                }
            });
        }
    </script>
</body>
</html>
