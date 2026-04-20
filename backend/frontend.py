import streamlit as st
import requests
import time

# Define your Django API endpoints
DJANGO_UPLOAD_URL = "http://127.0.0.1:8000/api/upload/"
DJANGO_CHAT_URL = "http://127.0.0.1:8000/api/chat/"
DJANGO_CLEAR_URL = "http://127.0.0.1:8000/api/clear/"

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Br1th AI", page_icon="🤖", layout="centered")

# --- CUSTOM CSS: BLACK MINIMALIST FUTURISTIC THEME ---
st.markdown("""
    <style>
    /* Global Dark/Futuristic Theme */
    .stApp {
        background-color: #050505;
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide default Streamlit headers/footers */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Center container width */
    .block-container {
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Style the Title & Badge */
    .header-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #FFFFFF;
        display: inline-block;
    }
    .badge {
        background-color: #1A1A1A;
        color: #888;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        border: 1px solid #333;
        float: right;
        margin-top: 10px;
    }

    /* Buttons Styling */
    div.stButton > button {
        border-radius: 8px;
        height: 45px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    /* Secondary Button (Clear) */
    div.stButton > button:first-child {
        background-color: transparent;
        border: 1px solid #333;
        color: #FF4A4A;
    }
    div.stButton > button:first-child:hover {
        border-color: #FF4A4A;
        box-shadow: 0 0 10px rgba(255, 74, 74, 0.2);
    }
    /* Primary Button (Analyze) */
    div.stButton > button[kind="primary"] {
        background-color: #0A66C2; /* Deep Blue */
        border: none;
        color: white;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #0084FF; /* Neon Blue Glow */
        box-shadow: 0 0 15px rgba(0, 132, 255, 0.4);
    }

    /* Compact File Uploader */
    [data-testid="stFileUploader"] {
        padding: 0;
    }
    [data-testid="stFileUploader"] section {
        padding: 5px;
        background-color: transparent;
        border: 1px dashed #333;
        border-radius: 8px;
    }
    
    /* Divider line */
    hr {
        border-color: #1A1A1A;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    /* Chat Input Bar */
    [data-testid="stChatInput"] {
        border-color: #333;
        background-color: #0E0E0E;
    }

    /* WhatsApp Typing Animation */
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 5px;
        padding: 10px 15px;
        background-color: #1A1A1A;
        border: 1px solid #333;
        border-radius: 15px;
        width: fit-content;
        margin-bottom: 10px;
    }
    .typing-indicator span {
        width: 6px;
        height: 6px;
        background-color: #0084FF;
        border-radius: 50%;
        animation: bounce 1.4s infinite ease-in-out both;
    }
    .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
    .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
    </style>
""", unsafe_allow_html=True)

# --- GENERATOR FOR LIVE TYPING EFFECT ---
def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# --- UI HEADER ---
st.markdown("""
    <div>
        <span class="header-title">Br1th AI Assistant</span>
        <span class="badge">gemma • RAG</span>
    </div>
""", unsafe_allow_html=True)
st.write("---")

# --- INLINE CONTROL PANEL (Matches Screenshot) ---
col1, col2, col3 = st.columns([4, 1.2, 1.2])

with col1:
    uploaded_file = st.file_uploader("Upload", type=['pdf', 'png', 'jpg', 'jpeg'], label_visibility="collapsed")
    
with col2:
    analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

with col3:
    clear_btn = st.button("Clear", use_container_width=True)

st.write("---")

# --- LOGIC FOR BUTTONS ---
# Using st.toast instead of large success boxes keeps the minimalist feel!
if analyze_btn:
    if uploaded_file is not None:
        with st.spinner("Extracting & Vectorizing..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(DJANGO_UPLOAD_URL, files=files)
                if response.status_code == 200:
                    st.toast(f"✅ {uploaded_file.name} added to database!", icon="✅")
                else:
                    st.error(f"❌ Error: {response.json().get('error', 'Unknown error')}")
            except requests.exceptions.ConnectionError:
                st.error("🚨 Django server is not running!")
    else:
        st.toast("⚠️ Please upload a file first.", icon="⚠️")

if clear_btn:
    with st.spinner("Clearing Database..."):
        try:
            response = requests.post(DJANGO_CLEAR_URL)
            if response.status_code == 200:
                st.toast("✅ Database cleared successfully!", icon="🗑️")
                st.session_state.messages =[]
                time.sleep(1) # Brief pause so user sees the toast before reload
                st.rerun() 
            else:
                st.error("❌ Error clearing database.")
        except requests.exceptions.ConnectionError:
            st.error("🚨 Django server is not running.")


# --- MAIN CHAT WINDOW ---
if "messages" not in st.session_state:
    st.session_state.messages =[]

# Show empty state message if no chat history
if len(st.session_state.messages) == 0:
    st.markdown("<div style='text-align: center; color: #555; margin-top: 50px; font-style: italic;'>Upload a document and ask a question to start.</div>", unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "timer" in message:
            st.caption(message["timer"])

# --- CHAT INPUT & GENERATION ---
if prompt := st.chat_input("Ask a question..."):
    # 1. Show user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Prepare AI Response
    with st.chat_message("assistant"):
        # WhatsApp Typing Animation
        typing_placeholder = st.empty()
        typing_placeholder.markdown("""
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        """, unsafe_allow_html=True)

        try:
            start_time = time.time()
            
            response = requests.post(
                DJANGO_CHAT_URL, 
                json={
                    "question": prompt,
                    "history": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                }
            )
            
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            timer_text = f"⏱️ Temps : {duration} s"
            
            typing_placeholder.empty() # Remove typing dots
            
            if response.status_code == 200:
                answer = response.json().get("answer", "No answer found.")
                
                if answer.startswith("🚨"):
                    st.error(answer)
                else:
                    st.write_stream(stream_data(answer))
                    st.caption(timer_text)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "timer": timer_text
                    })
            else:
                st.error("Error communicating with the AI backend.")
                
        except requests.exceptions.ConnectionError:
            typing_placeholder.empty()
            st.error("🚨 Django server is not running!")