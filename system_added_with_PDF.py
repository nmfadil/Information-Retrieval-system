


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
#import fitz  # PyMuPDF
#from sentence_transformers import SentenceTransformer
#import faiss
#import numpy as np
#import textwrap
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
#from langchain.embeddings import HuggingFaceInstructEmbeddings
#from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings
#from langchain.embeddings import HuggingFaceHub
#from langchain.vectorstores import FAISS
from langchain_community.vectorstores import FAISS

api_key = st.secrets["CS_API_KEY"]

cse_id = st.secrets["CSE_ID"]


hugg_token = st.secrets["HUGGINGFACEHUB_API_TOKEN"]
# Google Custom Search API setup
API_KEY = api_key
CSE_ID = cse_id
HF_TOKEN = hugg_token



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
        
        
        
        
        


# ========== For PDF ==========


def get_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content
    return text

def get_text_chunks(text):
    splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len
    )
    return splitter.split_text(text)
# def get_text_chunks(text, chunk_size=1500, chunk_overlap=100):
#     sentences = sent_tokenize(text)
    
#     chunks = []
#     current_chunk = ""

#     for sentence in sentences:
#         # Accumulate sentences until reaching chunk size
#         if len(current_chunk) + len(sentence) <= chunk_size:
#             current_chunk += " " + sentence
#         else:
#             chunks.append(current_chunk.strip())

#             # Add overlap if needed
#             if chunk_overlap > 0 and len(chunks) > 0:
#                 overlap = chunks[-1][-chunk_overlap:]
#                 current_chunk = overlap + " " + sentence
#             else:
#                 current_chunk = sentence

#     # Add final chunk
#     if current_chunk:
#         chunks.append(current_chunk.strip())

#     return chunks



# def get_vectorstore(chunks):
#     # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
#     # # embeddings = HuggingFaceHub(
#     # #     repo_id="hkunlp/instructor-xl", 
#     # #     model_kwargs={"temperature": 0.5, "max_length": 512}
#     # # )
#     # return FAISS.from_texts(texts=chunks, embedding=embeddings)
#     try:
#         embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
#         vectorstore = FAISS.from_texts(texts=chunks, embedding=embeddings)
#     except TypeError as e:
#         if "token" in str(e):
#             st.warning("Encountered model init bug. Retrying...")
#             # Retry without clearing cache, will likely succeed on rerun
#             st.rerun()
#         else:
#             raise e
#     return vectorstore
def get_vectorstore(chunks):
    try:
        embeddings = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-mpnet-base-v2",  # or any hosted model
            task="feature-extraction",
            huggingfacehub_api_token=HF_TOKEN  # via .env or secrets
        )
        vectorstore = FAISS.from_texts(texts=chunks, embedding=embeddings)
    except Exception as e:
        raise RuntimeError(f"❌ Failed to build vectorstore: {e}")
    return vectorstore





# ========== Main App ==========





# Streamlit app
st.title("Information Retrieval System")

# --- Add this at the top (after st.title) ---
mode = st.selectbox("Choose Retrieval Mode", ["Wikipedia IR", "PDF IR"])

# ========== WIKIPEDIA IR MODE ==========
if mode == "Wikipedia IR":
    
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

# ========== PDF IR MODE ==========
elif mode == "PDF IR":
    st.subheader("📄 PDF-Based IR")

    uploaded_pdf = st.file_uploader("Upload a PDF document", type=["pdf"])

    if uploaded_pdf:
        st.success("✅ PDF uploaded successfully.")
        current_filename = uploaded_pdf.name

        # Auto-reset if a new file is uploaded
        if st.session_state.get("pdf_filename") != current_filename:
            st.session_state.clear()  # Clear everything related to the previous session
            st.session_state["pdf_filename"] = current_filename

        if "vectorstore" not in st.session_state:
            with st.spinner("📄 Extracting, chunking, and embedding..."):
                try:
                    # Step 1: Extract
                    raw_text = get_pdf_text(uploaded_pdf)
                    st.session_state["pdf_text"] = raw_text

                    # Step 2: Chunk
                    chunks = get_text_chunks(raw_text)
                    st.session_state["pdf_chunks"] = chunks

                    # Step 3: Embed & Store
                    vectorstore = get_vectorstore(chunks)
                    st.session_state["vectorstore"] = vectorstore

                    st.success("✅ Vectorstore ready. You can now ask questions from this PDF.")
                    #st.text_area("📖 Preview Extracted Text", raw_text[:2000], height=200)
                    st.subheader("🧩 Text Chunks Preview")
                    for i, chunk in enumerate(chunks):
                        st.markdown(f"**Chunk {i+1}:**")
                        st.code(chunk, language="markdown")

                except Exception as e:
                    st.error(f"❌ Failed to process PDF: {e}")
        else:
            st.info("📄 Text already extracted.")
            #st.text_area("📖 Preview Extracted Text", st.session_state["pdf_text"][:3000], height=200)
        # 📤 User Query
        user_query = st.text_input("🔎 Ask a question based on this PDF")

        if user_query and st.session_state.get("vectorstore"):
            with st.spinner("🧠 Performing semantic search..."):
                try:
                    # Retrieve top relevant chunks
                    relevant_docs = st.session_state["vectorstore"].similarity_search(user_query, k=3)

                    # Extract and display content
                    for i, doc in enumerate(relevant_docs, 1):
                        st.markdown(f"**Match {i}:**")
                        st.write(doc.page_content)
                        st.markdown("---")

                except Exception as e:
                    st.error(f"❌ Semantic search failed: {e}")

    else:
        st.warning("📥 Please upload a PDF to proceed.")
