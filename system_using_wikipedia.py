import streamlit as st
import requests
from googleapiclient.discovery import build
from gtts import gTTS
import os
import io
from PIL import Image
import speech_recognition as sr
import wikipedia
import re

from dotenv import load_dotenv

# Load API key securely
load_dotenv()
api_key = os.getenv("CS_API_KEY")
if not api_key:
    st.error("Custom Search Api key not found! Please set it in a .env file.")
    st.stop()
cse_id = os.getenv("CSE_ID")
if not cse_id:
    st.error("Custom Search Engine ID not found! Please set it in a .env file.")
    st.stop()

# Google Custom Search API setup
API_KEY = api_key
CSE_ID = cse_id




def clean_query(query):
    # Remove phrases like "what is", "explain", etc.
    query = query.lower()
    query = re.sub(r"^(what is|who is|define|explain|tell me about)\s+", "", query)
    return query.strip().capitalize()


def fetch_answer(query):
    try:
        query = clean_query(query)

        # Step 1: Get best matching title
        search_results = wikipedia.search(query)
        if not search_results:
            return "Sorry, no results found."

        best_title = search_results[0]

        # Step 2: Fetch summary of top result
        summary = wikipedia.summary(best_title, sentences=2)
        return summary

    except wikipedia.exceptions.DisambiguationError as e:
        return f"Too broad. Try one of these: {e.options[:3]}"
    except wikipedia.exceptions.PageError:
        return "Couldn't find a valid Wikipedia page."
    except Exception:
        return "An error occurred while retrieving the answer."

def fetch_image(query):
    try:
        service = build("customsearch", "v1", developerKey=API_KEY)
        res = service.cse().list(q=query, cx=CSE_ID, searchType="image", num=1).execute()
        image_url = res['items'][0]['link']
        return image_url
    except Exception:
        return None
    
def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    audio_file = "output.mp3"
    tts.save(audio_file)
    return audio_file

def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎤 Listening... please speak now.")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)
            text = recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return "⏱️ Listening timed out. Please try again."
        except sr.UnknownValueError:
            return "😕 Sorry, I couldn't understand your speech."
        except sr.RequestError:
            return "❌ Speech service is unreachable. Please check your internet."


# Streamlit app
st.title("Information Retrieval System")

# Input options
input_method = st.radio("Choose input method:", ("Text", "Speech"))
query = ""

if input_method == "Text":
    query = st.text_input("Enter your query (e.g., 'What is AI?')")
else:
    spoken_text = ""
    if st.button("🎙️ Record Speech"):
        spoken_text = speech_to_text()
        st.write("🗣️ You said:", spoken_text)
    
    if spoken_text and not spoken_text.startswith(("⏱️", "😕", "❌")):
        query = spoken_text
    elif spoken_text:
        st.warning("Speech input failed. Please try again.")
        if st.button("🔁 Try Again"):
            spoken_text = speech_to_text()
            st.write("🗣️ You said:", spoken_text)
            if not spoken_text.startswith(("⏱️", "😕", "❌")):
                query = spoken_text

# Process query and display results
if query and st.button("Get Answer"):
    with st.spinner("Fetching answer..."):
        query = clean_query(query)
        answer, image_url = fetch_answer(query), fetch_image(query)
        
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