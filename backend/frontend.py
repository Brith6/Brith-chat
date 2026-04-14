import streamlit as st
import requests

# Define your Django API endpoints
DJANGO_UPLOAD_URL = "http://127.0.0.1:8000/api/upload/"
DJANGO_CHAT_URL = "http://127.0.0.1:8000/api/chat/"
DJANGO_CLEAR_URL = "http://127.0.0.1:8000/api/clear/"

st.set_page_config(page_title="Local RAG Chatbot", page_icon="🤖")
st.title("🤖 Local AI Document Chatbot")

# --- SIDEBAR: FILE UPLOAD ---
with st.sidebar:
    st.header("📂 Upload Documents")
    st.write("Upload PDFs or Images (PNG/JPG) to build the database.")
    
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    if st.button("Process & Save File"):
        if uploaded_file is not None:
            with st.spinner("Processing file, extracting text, and generating vectors..."):
                # Prepare the file to be sent to Django
                files = {
                    "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                }
                
                try:
                    # Send POST request to Django Upload Endpoint
                    response = requests.post(DJANGO_UPLOAD_URL, files=files)
                    
                    if response.status_code == 200:
                        st.success(f"✅ {uploaded_file.name} added to database!")
                    else:
                        st.error(f"❌ Error: {response.json().get('error', 'Unknown error')}")
                except requests.exceptions.ConnectionError:
                    st.error("🚨 Django server is not running! Please start it on port 8000.")
        else:
            st.warning("⚠️ Please upload a file first.")
        
    st.divider()
    st.header("⚙️ Settings")
    if st.button("🗑️ Vider la base de données", type="primary"):
        with st.spinner("Nettoyage en cours..."):
            try:
                response = requests.post(DJANGO_CLEAR_URL)
                
                if response.status_code == 200:
                    st.success("✅ Base de données effacée avec succès !")
                    
                    # 1. Clear the chat history on the screen
                    st.session_state.messages =[]
                    
                    # 2. Refresh the Streamlit interface automatically
                    st.rerun() 
                    
                else:
                    st.error(f"❌ Erreur: {response.json().get('error', 'Erreur inconnue')}")
                    
            except requests.exceptions.ConnectionError:
                st.error("🚨 Le serveur Django n'est pas en cours d'exécution. Lancez le sur le port 8000.")

# --- MAIN WINDOW: CHAT INTERFACE ---
st.subheader("💬 Chat with your Data")

# Initialize chat history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages =[]

# Display previous chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about your uploaded files..."):
    # 1. Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    
    # 2. Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 3. Send the question to Django backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    DJANGO_CHAT_URL, 
                    json={"question": prompt}
                )
                
                if response.status_code == 200:
                    answer = response.json().get("answer", "No answer found.")
                    st.markdown(answer)
                    
                    # 4. Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("Error communicating with the AI backend.")
            except requests.exceptions.ConnectionError:
                st.error("🚨 Django server is not running! Please start it on port 8000.")