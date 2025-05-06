from flask import Flask, render_template, request, jsonify, send_file
import os
import yt_dlp
import threading

app = Flask(__name__)

SOUND_DIR = "sounds"
if not os.path.exists(SOUND_DIR):
    os.makedirs(SOUND_DIR)

sounds = {}
key_mappings = {}

def download_audio(url, key):
    try:
        filename = f"{SOUND_DIR}/{key}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        sounds[key] = filename
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    for mapping in data:
        if mapping['url'] and mapping['key']:
            key_mappings[mapping['key']] = mapping['url']
            threading.Thread(target=download_audio, args=(mapping['url'], mapping['key'])).start()
    return jsonify({"status": "success"})

@app.route('/play/<key>')
def play(key):
    if key in sounds and os.path.exists(sounds[key]):
        return send_file(sounds[key], mimetype='audio/mpeg')
    return jsonify({"status": "error", "message": "Sound not found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
