import os
import faiss
import numpy as np
import pytesseract
from PIL import Image
import PyPDF2
from sentence_transformers import SentenceTransformer
import requests

from .models import Document, DocumentChunk

print("Loading Embedding Model...")
# We STILL need this small model to convert text to vectors for FAISS
embedder = SentenceTransformer('all-MiniLM-L6-v2') 

# --- PERSISTENCE SETUP ---
FAISS_INDEX_PATH = "faiss_index.bin"
EMBEDDING_DIMENSION = 384

if os.path.exists(FAISS_INDEX_PATH):
    vector_db = faiss.read_index(FAISS_INDEX_PATH)
else:
    vector_db = faiss.IndexFlatL2(EMBEDDING_DIMENSION)

#[KEEP YOUR 'extract_text_from_file' FUNCTION EXACTLY THE SAME]
def extract_text_from_file(file_path, file_type):
    text = ""
    if file_type in ['image/jpeg', 'image/png']:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
    elif file_type == 'application/pdf':
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    return text

#[KEEP YOUR 'process_and_store_document' FUNCTION EXACTLY THE SAME]
def process_and_store_document(text, file_name):
    if not text.strip():
        return
    doc_obj = Document.objects.create(file_name=file_name)
    words = text.split()
    chunk_size = 100
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    embeddings = embedder.encode(chunks)
    start_id = vector_db.ntotal
    vector_db.add(np.array(embeddings))
    faiss.write_index(vector_db, FAISS_INDEX_PATH)
    for i, chunk_text in enumerate(chunks):
        DocumentChunk.objects.create(
            document=doc_obj,
            text_content=chunk_text,
            faiss_index_id=start_id + i
        )

# [UPDATE THIS FUNCTION TO USE DEEPSEEK via OLLAMA]
def ask_chatbot(question):
    if vector_db.ntotal == 0:
        return "Je n'ai pas encore de documents dans ma base de données. Veuillez d'abord uploader un fichier."

    # 1. Embed the user's question
    question_vector = embedder.encode([question])
    distances, indices = vector_db.search(np.array(question_vector), k=3)
    
    # 2. Retrieve the text from Django Database
    retrieved_chunks = []
    for faiss_id in indices[0]:
        if faiss_id != -1:
            try:
                chunk = DocumentChunk.objects.get(faiss_index_id=faiss_id)
                retrieved_chunks.append(chunk.text_content)
            except DocumentChunk.DoesNotExist:
                continue
    context = "\n\n".join(retrieved_chunks)
    
    # 3. Create a clean French Prompt
    prompt = f"""Tu es un assistant IA professionnel. Réponds à la question en utilisant UNIQUEMENT le contexte fourni ci-dessous. Ne rajoute pas d'informations extérieures.
    
Contexte: 
{context}

Question: {question}
"""

    # 4. Send to local Ollama DeepSeek API
    ollama_url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma2", # The model you just downloaded
        "prompt": prompt,
        "stream": False # Tells Ollama to wait and send the complete answer at once
    }
    
    try:
        response = requests.post(ollama_url, json=payload)
        response.raise_for_status() # Check for errors
        
        # DeepSeek-R1 sometimes includes its "thinking process" inside <think> tags. 
        # This code removes the thinking tags so the user only sees the final answer.
        full_response = response.json()["response"]
        if "</think>" in full_response:
            final_answer = full_response.split("</think>")[-1].strip()
            return final_answer
        return full_response.strip()

    except requests.exceptions.ConnectionError:
        return "🚨 Erreur : Ollama n'est pas en cours d'exécution. Veuillez vérifier que l'application Ollama est ouverte sur votre ordinateur."
    
def clear_database():
    """Clears the SQLite Database, FAISS RAM index, and FAISS disk file."""
    try:
        # 1. Delete all text from the Django Database
        # (Because we used 'CASCADE' in our models, deleting Documents 
        # automatically deletes all the connected DocumentChunks)
        Document.objects.all().delete()
        
        # 2. Clear the FAISS index currently running in RAM
        vector_db.reset()
        
        # 3. Overwrite the FAISS file on your hard drive with the empty index
        faiss.write_index(vector_db, FAISS_INDEX_PATH)
        
        return True
    except Exception as e:
        print(f"Error clearing database: {e}")
        return False