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

# from dotenv import load_dotenv

# # Load API key securely
# load_dotenv()
api_key = st.secrets["CS_API_KEY"]
# if not api_key:
#     st.error("Custom Search Api key not found! Please set it in a .env file.")
#     st.stop()
cse_id = st.secrets["CSE_ID"]
# if not cse_id:
#     st.error("Custom Search Engine ID not found! Please set it in a .env file.")
#     st.stop()

# Google Custom Search API setup
API_KEY = api_key
CSE_ID = cse_id


def clean_query(query):
    # Remove phrases like "what is", "explain", etc.
    query = query.lower()
    query = re.sub(r"^(what is|who is|define|explain|tell me about)\s+", "", query)
    return query.strip().capitalize()


def fetch_wiki_summaries(query, index=0):
    try:
        query = clean_query(query)
        search_results = wikipedia.search(query)

        if not search_results:
            return [], "Sorry, no results found."

        titles = search_results[:3]
        best_title = titles[index % len(titles)]  # Safe looping

        summary = wikipedia.summary(best_title, sentences=2)
        return titles, f"📘 *{best_title}*:\n\n{summary}"

    except wikipedia.exceptions.DisambiguationError as e:
        return [], f"Too broad. Try one of these: {e.options[:3]}"
    except wikipedia.exceptions.PageError:
        return [], "Couldn't find a valid Wikipedia page."
    except Exception:
        return [], "An error occurred while retrieving the answer."


# After fetching results from Google Custom Search
def fetch_images(query):
    try:
        service = build("customsearch", "v1", developerKey=API_KEY)
        res = service.cse().list(q=query, cx=CSE_ID, num=5).execute()

        image_urls = []
        for item in res.get("items", []):
            img_url = item.get('pagemap', {}).get('cse_image', [{}])[0].get('src')
            if img_url:
                image_urls.append(img_url)
        return image_urls
    except Exception:
        return []
    
def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp

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
# In your Streamlit code
if "img_index" not in st.session_state:
    st.session_state.img_index = 0
if "img_urls" not in st.session_state:
    st.session_state.img_urls = []
# Input options
input_method = st.radio("Choose input method:", ("Text", "Speech"))
query = ""

if input_method == "Text":
    query = st.text_input("Enter your query (e.g., 'What is AI?')")
else:
    spoken_text = ""
    if st.button("🎙️ Record Speech"):
        spoken_text = speech_to_text()
        
    
    # Allow users to refine their speech input as needed before hitting "Get Answer"
    # if spoken_text:
    #     if not spoken_text.startswith(("⏱️", "😕", "❌")):
    #         query = spoken_text
    #         st.write("🗣️ You said:", spoken_text)
    #     else:
    #         query = ""
    #         st.warning(spoken_text)
    if spoken_text:
        query = spoken_text if not spoken_text.startswith(("⏱️", "😕", "❌")) else ""
        (st.write("🗣️ You said:", spoken_text) if query else st.warning(spoken_text))

# Handle session state
if "wiki_titles" not in st.session_state:
    st.session_state.wiki_titles = []
if "wiki_index" not in st.session_state:
    st.session_state.wiki_index = 0
    
# Process query and display results
if query and st.button("Get Answer"):
    with st.spinner("Fetching answer..."):
        query = clean_query(query)

        # Get Wikipedia titles and summary
        titles, summary = fetch_wiki_summaries(query, index=0)
        
        # Save for later cycling
        st.session_state.wiki_titles = titles
        st.session_state.wiki_index = 0
        st.session_state.answer = summary

        # Fetch images
        st.session_state.img_urls = fetch_images(query)
        st.session_state.img_index = 0

        # Generate and play TTS audio
        audio_bytes = text_to_speech(summary)
        st.audio(audio_bytes, format='audio/mp3')


# Show the stored answer (if exists)
if "answer" in st.session_state:
    st.markdown(st.session_state.answer)

# Allow rotating through alternative wiki articles
if st.session_state.get("wiki_titles") and len(st.session_state.wiki_titles) > 1:
    if st.button("🔁 Try Next Article"):
        st.session_state.wiki_index += 1
        _, summary = fetch_wiki_summaries(query, st.session_state.wiki_index)
        st.session_state.answer = summary
        st.markdown(summary)

        # Optional: Refresh audio on switch
        audio_bytes = text_to_speech(summary)
        st.audio(audio_bytes, format='audio/mp3')

# Show image and allow cycling
if st.session_state.img_urls:
    img_url = st.session_state.img_urls[st.session_state.img_index]
    try:
        response = requests.get(img_url, timeout=5)
        img = Image.open(io.BytesIO(response.content))
        st.image(img, caption=f"Related Image ({st.session_state.img_index + 1}/{len(st.session_state.img_urls)})")
    except Exception:
        st.warning("❌ Could not load the current image.")

    if st.button("➡️ Next Image"):
        st.session_state.img_index = (st.session_state.img_index + 1) % len(st.session_state.img_urls)

