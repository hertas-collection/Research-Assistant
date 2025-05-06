from flask import Flask, render_template, request, jsonify
import os
from pytube import YouTube
import pygame
import threading
import time

app = Flask(__name__)
pygame.mixer.init()

SOUND_DIR = "sounds"
if not os.path.exists(SOUND_DIR):
    os.makedirs(SOUND_DIR)

sounds = {}
key_mappings = {}

def download_audio(url, key):
    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        filename = f"{SOUND_DIR}/{key}.mp3"
        audio_stream.download(output_path=SOUND_DIR, filename=f"{key}.mp3")
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
    if key in sounds:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        pygame.mixer.music.load(sounds[key])
        pygame.mixer.music.play()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Sound not found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
