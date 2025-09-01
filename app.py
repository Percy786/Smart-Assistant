from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import pywhatkit
import os
import requests
import pytz
from datetime import datetime
from memory_logic import handle_memory_input, recall
import webbrowser
import re
import platform
import subprocess

# Volume Control Functions
def change_volume_windows(direction):
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    
    current = volume.GetMasterVolumeLevelScalar()
    step = 0.1  # 10%

    if direction == "increase":
        volume.SetMasterVolumeLevelScalar(min(current + step, 1.0), None)
    elif direction == "decrease":
        volume.SetMasterVolumeLevelScalar(max(current - step, 0.0), None)

def change_volume_linux(direction):
    if direction == "increase":
        subprocess.call(["amixer", "-D", "pulse", "sset", "Master", "5%+"])
    elif direction == "decrease":
        subprocess.call(["amixer", "-D", "pulse", "sset", "Master", "5%-"])

def change_volume(direction):
    os_name = platform.system().lower()
    if "windows" in os_name:
        change_volume_windows(direction)
    elif "linux" in os_name:
        change_volume_linux(direction)
    else:
        print("Volume control not supported on this OS.")

# Flask App Setup
app = Flask(__name__)

# Gemini setup
genai.configure(api_key="AIzaSyDEdizK87WSg1rWyUQ-G1F9dY2cwLjEC6g")
model = genai.GenerativeModel('gemini-1.5-flash-8b')

# WeatherAPI Key
WEATHERAPI_KEY = "Use you own API : ) "

# File paths
input_file_path = 'Input.txt'
output_file_path = 'Output.txt'

# Weather Function
def get_weather(city="Patna"):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q={city}"
        response = requests.get(url).json()
        location = response["location"]["name"]
        country = response["location"]["country"]
        temp_c = response["current"]["temp_c"]
        condition = response["current"]["condition"]["text"]
        return f"The current weather in {location}, {country} is {temp_c}°C with {condition.lower()}."
    except:
        return "Sorry, I couldn't get the weather data right now."

# Time Function
def get_time(timezone_str="Asia/Kolkata"):
    try:
        now = datetime.now(pytz.timezone(timezone_str))
        return now.strftime("The current time is %I:%M %p.")
    except:
        return "Sorry, I couldn't get the time right now."

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('message', '').lower()

    # Save input
    with open(input_file_path, 'a') as input_file:
        input_file.write(user_input + '\n')

    # Memory Logic
    memory_response = handle_memory_input(user_input)
    if memory_response:
        return jsonify({"reply": memory_response})

    if "what is my name" in user_input:
        return jsonify({"reply": f"Your name is {recall('user_name')}."})

    if "what is my favorite color" in user_input:
        return jsonify({"reply": f"Your favorite color is {recall('favorite_color')}."})

    # Play YouTube
    if user_input.startswith("play "):
        video_query = user_input[5:]
        try:
            pywhatkit.playonyt(video_query)
            reply = f"Playing '{video_query}' on YouTube!"
        except:
            reply = "Sorry, I couldn't open the video."

    elif user_input.endswith("your name"):
        reply = "my name is A.L.P.H.A"

    elif user_input.endswith("what does alpha stand for"):
            reply = "Adaptive learning Personal Helping Assistant"

    # Open Website
    elif user_input.startswith("open "):
        site_name = user_input[5:].strip()
        known_sites = {
            "google": "https://www.google.com",
            "instagram": "https://www.instagram.com",
            "facebook": "https://www.facebook.com",
            "twitter": "https://www.twitter.com",
            "youtube": "https://www.youtube.com",
            "github": "https://www.github.com",
            "snapchat": "https://www.cnapchat.com"
        }
        url = known_sites.get(site_name)
        if url:
            webbrowser.open(url)
            reply = f"Opening {site_name.title()}..."
        else:
            reply = f"Sorry, I don’t know how to open '{site_name}'."

    # Weather
    elif "weather" in user_input:
        match = re.search(r"weather(?: in)? ([a-zA-Z\s]+)", user_input)
        city = match.group(1) if match else "Patna"
        reply = get_weather(city)

    # Time
    elif "time" in user_input:
        reply = get_time()

    # Volume Control
    elif "increase volume" in user_input or "turn up the volume" in user_input:
        change_volume("increase")
        reply = "Increased the system volume."

    elif "decrease volume" in user_input or "turn down the volume" in user_input:
        change_volume("decrease")
        reply = "Decreased the system volume."

    elif "increase system volume" in user_input or "turn up the volume" in user_input:
        change_volume("increase")
        reply = "Increased the system volume."

    elif "decrease system volume" in user_input or "turn down the volume" in user_input:
        change_volume("decrease")
        reply = "Decreased the system volume."

    # Fallback to Gemini
    else:
        try:
            response = model.generate_content(user_input + " form full sentences but dont use uneccesssary words, dont use punctuations")
            reply = response.text
        except:
            reply = "Sorry, there was a connecting to the asistant."

    # Save Output
    with open(output_file_path, 'a') as output_file:
        output_file.write(reply + '\n')

    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
