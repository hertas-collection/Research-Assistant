from flask import Flask, render_template, request, jsonify
import re
from typing import List, Dict
from datetime import datetime

class User:
    def __init__(self, name: str):
        self.name = name
        self.requests: List[Dict] = []
        self.tone_score = 0

    def update_tone(self, message: str) -> None:
        casual_markers = len(re.findall(r'(!+|\?+|lol|haha|:D|;)|hey|hi', message.lower()))
        formal_markers = len(re.findall(r'(please|would you|could you|sincerely|regards)', message.lower()))
        self.tone_score = max(-1, min(1, self.tone_score + (casual_markers - formal_markers) * 0.2))

class ResearchAssistant:
    def __init__(self):
        self.users = {}

    def get_response_style(self, user) -> tuple:
        if user.tone_score < -0.3:
            greeting = f"Good day, {user.name}."
            closing = "Best regards,"
        elif user.tone_score > 0.3:
            greeting = f"Hey {user.name}! 😊"
            closing = "Cheers!"
        else:
            greeting = f"Hi {user.name}!"
            closing = "Best,"
        return (greeting, closing)

    def process_request(self, user, request: str) -> str:
        user.requests.append({
            "timestamp": datetime.now(),
            "request": request
        })
        user.update_tone(request)
        greeting, closing = self.get_response_style(user)

        if "previous requests" in request.lower():
            return self._format_previous_requests(user)

        response = f"{greeting}\n\nI've noted your request. How can I help you with this?\n\n{closing}"
        return response

    def _format_previous_requests(self, user) -> str:
        greeting, closing = self.get_response_style(user)
        response = []
        for req in user.requests[:-1]:
            timestamp = req["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            response.append(f"[{timestamp}] {req['request']}")
        return "\n".join(response)


app = Flask(__name__)
assistant = ResearchAssistant()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.json.get('name')
    if name:
        user = User(name.capitalize())
        assistant.users[name] = user
        return jsonify({"success": True, "message": f"Welcome, {name}!"})
    return jsonify({"success": False, "message": "Please provide a name"})

@app.route('/request', methods=['POST'])
def handle_request():
    name = request.json.get('name')
    user_request = request.json.get('request')

    if not name or name not in assistant.users:
        return jsonify({"success": False, "message": "Please register first"})

    user = assistant.users[name]
    response = assistant.process_request(user, user_request)

    if "previous requests" in user_request.lower():
        return jsonify({"success": True, "message": "\n".join(response), "type": "history"})

    return jsonify({"success": True, "message": response, "type": "response"})

if __name__ == '__main__':
    app.run(debug=True)
