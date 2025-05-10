
# versus ir_system.py
# 1. Transformer-Based Answer Refinement
# this version uses a transformers-based question-answering model (distilbert-base-uncased-distilled-squad) to refine the Google snippet into a more direct answer.
# 2. Improved UX Labels
# This version clearly labels the refined answer and differentiates it from the raw snippet.
# More user-friendly wording like "Fetching and refining answer…" versus "Fetching answer…".
import streamlit as st
import requests
from googleapiclient.discovery import build
from gtts import gTTS
import os
import io
from PIL import Image
import speech_recognition as sr
from dotenv import load_dotenv
#from transformers import pipeline

# Load API key securely
load_dotenv()
api_key = os.getenv("CS_API_KEY")
if not api_key:
    st.error("Custom Search API key not found! Please set it in a .env file.")
    st.stop()
cse_id = os.getenv("CSE_ID")
if not cse_id:
    st.error("Custom Search Engine ID not found! Please set it in a .env file.")
    st.stop()

# Google Custom Search API setup
API_KEY = api_key
CSE_ID = cse_id

# Initialize the question-answering pipeline
#qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

def google_search(query):
    service = build("customsearch", "v1", developerKey=API_KEY)
    res = service.cse().list(q=query, cx=CSE_ID, num=1).execute()
    snippet = res['items'][0]['snippet']  # Raw snippet as context
    image_url = res['items'][0].get('pagemap', {}).get('cse_image', [{}])[0].get('src', None)
    return snippet, image_url

def refine_answer(query, context):
    # Use the Transformer model to extract a concise answer
    #result = qa_pipeline(question=query, context=context)
    return raw_answer#result['answer']

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
    with st.spinner("Fetching and refining answer..."):
        # Get raw snippet and image from Google
        raw_answer, image_url = google_search(query)
        
        # Refine the answer using the Transformer model
        refined_answer = refine_answer(query, raw_answer)
        
        # Display refined answer
        st.write("Answer:", refined_answer)
        
        # Generate and display audio with controls
        audio_file = text_to_speech(refined_answer)
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