# # https://github.com/ayshajamjam/Enhanced-Google-Search-API-Information-Retrieval?tab=readme-ov-file
# # Demo https://www.youtube.com/watch?v=auG58f2L7qs

# import streamlit as st
# import requests
# from googleapiclient.discovery import build
# from gtts import gTTS
# import os
# # from playsound import playsound
# from pygame import mixer
# import time
# import speech_recognition as sr
# from PIL import Image
# import io

# from dotenv import load_dotenv

# # Load API key securely
# load_dotenv()
# api_key = os.getenv("CS_API_KEY")
# if not api_key:
#     st.error("Custom Search Api key not found! Please set it in a .env file.")
#     st.stop()
# cse_id = os.getenv("CSE_ID")
# if not api_key:
#     st.error("Custom Search Engine ID not found! Please set it in a .env file.")
#     st.stop()

# # Google Custom Search API setup
# API_KEY = api_key
# CSE_ID = cse_id

# def google_search(query):
#     service = build("customsearch", "v1", developerKey=API_KEY)
#     res = service.cse().list(q=query, cx=CSE_ID, num=1).execute()
#     snippet = res['items'][0]['snippet']  # Text answer
#     image_url = res['items'][0].get('pagemap', {}).get('cse_image', [{}])[0].get('src', None)  # Image URL
#     return snippet, image_url

# # def text_to_speech(text):
# #     tts = gTTS(text=text, lang='en')
# #     audio_file = "audio_output/output.mp3"
# #     tts.save(audio_file)
# #     playsound(audio_file)
# #     os.remove(audio_file)  # Clean up

# def text_to_speech(text):
#     tts = gTTS(text=text, lang='en')
#     audio_file = "audio_output/output.mp3"
#     tts.save(audio_file)
#     mixer.init()
#     mixer.music.load(audio_file)
#     mixer.music.play()
#     while mixer.music.get_busy():  # Wait for audio to finish playing
#         time.sleep(0.1)
#     mixer.music.stop()
#     mixer.quit()
#     os.remove(audio_file)  # Clean up


# def speech_to_text():
#     recognizer = sr.Recognizer()
#     with sr.Microphone() as source:
#         st.write("Listening...")
#         audio = recognizer.listen(source)
#         try:
#             text = recognizer.recognize_google(audio)
#             return text
#         except sr.UnknownValueError:
#             return "Sorry, I couldn't understand the audio."
#         except sr.RequestError:
#             return "Speech recognition service unavailable."

# # Streamlit app
# st.title("Information Retrieval System")

# # Input options
# input_method = st.radio("Choose input method:", ("Text", "Speech"))
# query = ""

# if input_method == "Text":
#     query = st.text_input("Enter your query (e.g., 'What is AI?')")
# else:
#     if st.button("Record Speech"):
#         query = speech_to_text()
#         st.write(f"You said: {query}")

# # Process query and display results
# if query and st.button("Get Answer"):
#     with st.spinner("Fetching answer..."):
#         answer, image_url = google_search(query)
        
#         # Display text answer
#         st.write("Answer:", answer)
        
#         # Speech output option
#         if st.button("Hear Answer"):
#             text_to_speech(answer)
        
#         # Display image
#         if image_url:
#             response = requests.get(image_url, stream=True)
#             img = Image.open(io.BytesIO(response.content))
#             st.image(img, caption="Related Image")
#         else:
#             st.write("No related image found.")


import streamlit as st
import requests
from googleapiclient.discovery import build
from gtts import gTTS
import os
import io
from PIL import Image
import speech_recognition as sr

from dotenv import load_dotenv

# Load API key securely
load_dotenv()
api_key = os.getenv("CS_API_KEY")
if not api_key:
    st.error("Custom Search Api key not found! Please set it in a .env file.")
    st.stop()
cse_id = os.getenv("CSE_ID")
if not api_key:
    st.error("Custom Search Engine ID not found! Please set it in a .env file.")
    st.stop()

# Google Custom Search API setup
API_KEY = api_key
CSE_ID = cse_id

def google_search(query):
    service = build("customsearch", "v1", developerKey=API_KEY)
    res = service.cse().list(q=query, cx=CSE_ID, num=1).execute()
    snippet = res['items'][0]['snippet']  # Text answer
    image_url = res['items'][0].get('pagemap', {}).get('cse_image', [{}])[0].get('src', None)  # Image URL
    return snippet, image_url

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    audio_file = "output.mp3"
    tts.save(audio_file)
    return audio_file

def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand the audio."
        except sr.RequestError:
            return "Speech recognition service unavailable."

# Streamlit app
st.title("Information Retrieval System")

# Input options
input_method = st.radio("Choose input method:", ("Text", "Speech"))
query = ""

if input_method == "Text":
    query = st.text_input("Enter your query (e.g., 'What is AI?')")
else:
    if st.button("Record Speech"):
        query = speech_to_text()
        st.write(f"You said: {query}")

# Process query and display results
if query and st.button("Get Answer"):
    with st.spinner("Fetching answer..."):
        answer, image_url = google_search(query)
        
        # Display text answer
        st.write("Answer:", answer)
        
        # Generate and display audio with controls
        audio_file = text_to_speech(answer)
        audio_bytes = open(audio_file, "rb").read()
        st.audio(audio_bytes, format="audio/mp3")
        os.remove(audio_file)  # Clean up
        
        # Display image
        if image_url:
            response = requests.get(image_url, stream=True)
            img = Image.open(io.BytesIO(response.content))
            st.image(img, caption="Related Image")
        else:
            st.write("No related image found.")