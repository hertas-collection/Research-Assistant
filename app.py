
from flask import Flask, request, jsonify
from datetime import datetime
import re
import requests
import os

class User:
    def __init__(self, name: str):
        self.name = name
        self.requests = []
        self.tone_score = 0

    def update_tone(self, message: str):
        casual_markers = len(re.findall(r'(!+|\?+|lol|haha|:D|;)|hey|hi', message.lower()))
        formal_markers = len(re.findall(r'(please|would you|could you|sincerely|regards)', message.lower()))
        self.tone_score = max(-1, min(1, self.tone_score + (casual_markers - formal_markers) * 0.2))

class ResearchAssistant:
    def __init__(self):
        self.users = {}

app = Flask(__name__)
assistant = ResearchAssistant()

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Research Assistant</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .chat-container { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 5px; }
            input[type="text"] { width: 70%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-right: 10px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .assistant { background: #e9ecef; }
            .user { background: #007bff; color: white; text-align: right; }
            #registration { text-align: center; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="text-align: center;">Research Assistant</h1>
            
            <div id="registration">
                <input type="text" id="nameInput" placeholder="Enter your name">
                <button onclick="register()">Register</button>
            </div>

            <div id="chat" style="display: none;">
                <div class="chat-container" id="chatContainer"></div>
                <div class="input-group">
                    <input type="text" id="requestInput" placeholder="Type your request here">
                    <button onclick="sendRequest()">Send</button>
                    <button onclick="getHistory()">View History</button>
                </div>
            </div>
        </div>

        <script>
            let userName = '';

            async function register() {
                const nameInput = document.getElementById('nameInput');
                const name = nameInput.value.trim();
                
                if (!name) {
                    alert('Please enter your name');
                    return;
                }

                const response = await fetch('/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name})
                });

                const data = await response.json();
                if (data.success) {
                    userName = name;
                    document.getElementById('registration').style.display = 'none';
                    document.getElementById('chat').style.display = 'block';
                    addMessage(data.message, 'assistant');
                }
            }

            async function sendRequest() {
                const requestInput = document.getElementById('requestInput');
                const request = requestInput.value.trim();
                
                if (!request) return;

                addMessage(request, 'user');
                requestInput.value = '';

                const response = await fetch('/request', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: userName, request})
                });

                const data = await response.json();
                if (data.success) {
                    addMessage(data.message, 'assistant');
                }
            }

            async function getHistory() {
                const response = await fetch('/request', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: userName, request: 'previous requests'})
                });

                const data = await response.json();
                if (data.success && data.type === 'history') {
                    data.message.split('\\n').forEach(msg => {
                        if (msg.trim()) addMessage(msg, 'assistant');
                    });
                }
            }

            function addMessage(message, type) {
                const chatContainer = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                messageDiv.textContent = message;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            document.getElementById('requestInput')?.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendRequest();
            });

            document.getElementById('nameInput')?.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') register();
            });
        </script>
    </body>
    </html>
    '''

@app.route('/register', methods=['POST'])
def register():
    name = request.json.get('name')
    if name:
        user = User(name.capitalize())
        assistant.users[name] = user
        return jsonify({"success": True, "message": f"Welcome, {name}! How can I help you today?"})
    return jsonify({"success": False, "message": "Please provide a name"})

@app.route('/request', methods=['POST'])
def handle_request():
    name = request.json.get('name')
    user_request = request.json.get('request')

    if not name or name not in assistant.users:
        return jsonify({"success": False, "message": "Please register first"})

    user = assistant.users[name]
    user.requests.append({"timestamp": datetime.now(), "request": user_request})

    if "previous requests" in user_request.lower():
        history = "\n".join([f"[{req['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}] {req['request']}" 
                           for req in user.requests[:-1]])
        return jsonify({"success": True, "message": history, "type": "history"})

    user.update_tone(user_request)
    tone = "formally" if user.tone_score < -0.3 else "casually" if user.tone_score > 0.3 else "neutrally"

    # Basic response generation
    response = "I'm not sure about that. Could you please rephrase your question?"
    
    # Simple pattern matching for responses
    user_request_lower = user_request.lower()
    if "hello" in user_request_lower or "hi" in user_request_lower:
        response = f"Hello {name}! How can I help you today?"
    elif "how are you" in user_request_lower:
        response = "I'm doing well, thank you for asking! How can I assist you?"
    elif "weather" in user_request_lower:
        response = "I apologize, but I don't have access to real-time weather data. You might want to check a weather service for that information."
    elif "help" in user_request_lower:
        response = "I can help you with various topics. Just ask me a question, and I'll do my best to assist you!"
    elif "bye" in user_request_lower or "goodbye" in user_request_lower:
        response = f"Goodbye {name}! Have a great day!"
    elif "thank" in user_request_lower:
        response = "You're welcome! Let me know if you need anything else."
    else:
        try:
            # Search Wikipedia for relevant information
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": user_request,
                "utf8": 1,
                "formatversion": 2
            }
            
            search_response = requests.get(search_url, params=params)
            search_data = search_response.json()
            
            if search_data["query"]["search"]:
                result = search_data["query"]["search"][0]
                title = result["title"]
                snippet = result["snippet"].replace('<span class="searchmatch">', '').replace('</span>', '')
                
                # Get full page content
                page_params = {
                    "action": "query",
                    "format": "json",
                    "titles": title,
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "formatversion": 2
                }
                
                page_response = requests.get(search_url, params=page_params)
                page_data = page_response.json()
                
                if page_data["query"]["pages"]:
                    extract = page_data["query"]["pages"][0].get("extract", "")
                    sentences = extract.split('. ')[:2]
                    response = f"{'. '.join(sentences)}."
                else:
                    response = snippet.strip()
            
        except Exception as e:
            print(f"Error during web search: {e}")
            response = f"I understand your request and will respond {tone}. How can I help you further?"

    return jsonify({"success": True, "message": response, "type": "response"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

    # Get the port from the environment variable, or default to 5000
    port = int(os.environ.get("PORT", 5000))

    app.run(host='0.0.0.0', port=port)
