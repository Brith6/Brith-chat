import os
import faiss
import numpy as np
import pytesseract
from PIL import Image
import PyPDF2
import fitz
from sentence_transformers import SentenceTransformer
import requests

from .models import Document, DocumentChunk

print("Loading Embedding Model...")
# Convert text to vectors for FAISS
embedder = SentenceTransformer('all-MiniLM-L6-v2') 

# --- PERSISTENCE SETUP ---
FAISS_INDEX_PATH = "faiss_index.bin"
EMBEDDING_DIMENSION = 384

if os.path.exists(FAISS_INDEX_PATH):
    vector_db = faiss.read_index(FAISS_INDEX_PATH)
else:
    vector_db = faiss.IndexFlatL2(EMBEDDING_DIMENSION)

def extract_text_from_file(file_path, file_type):
    text = ""
    if file_type in ['image/jpeg', 'image/png']:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
    elif file_type == 'application/pdf':
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    return text

def process_and_store_document(text, file_name):
    if not text.strip():
        return
    doc_obj = Document.objects.create(file_name=file_name)
    words = text.split()
    chunk_size = 300
    overlap = 50
    chunks =[]
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
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

def ask_chatbot(question, history=[]):
    if vector_db.ntotal == 0:
        return "Je n'ai pas encore de documents dans ma base de données. Veuillez d'abord uploader un fichier."

    # 1. Recherche dans FAISS (On cherche le contexte avec la nouvelle question)
    question_vector = embedder.encode([question])
    distances, indices = vector_db.search(np.array(question_vector), k=3)
    
    retrieved_chunks =[]
    for faiss_id in indices[0]:
        if faiss_id != -1:
            try:
                chunk = DocumentChunk.objects.get(faiss_index_id=faiss_id)
                retrieved_chunks.append(chunk.text_content)
            except DocumentChunk.DoesNotExist:
                continue
    context = "\n\n".join(retrieved_chunks)
    
    # 2. Prompt Système
    system_instruction = f"""You are a highly intelligent, multilingual AI assistant. 

    🔴 CRITICAL RULES 🔴
    1. STRICT CONTEXT: You must answer the user's questions using ONLY the information provided in the "Context from documents" below. Do not invent, guess, or add external information. 
    2. NO HALLUCINATION: If the answer is not contained in the context, you MUST clearly state that the document does not contain this information.
    3. UNIVERSAL LANGUAGE: You must AUTO-DETECT the language of the user's question and answer in the EXACT SAME LANGUAGE.
    
    Context from documents:
    {context}
    """

    # 3. Construction de la mémoire (L'historique)
    messages =[
        {"role": "system", "content": system_instruction}
    ]
    
    # L'IA lit les anciens messages et se souvient de la discussion !
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    messages.append({
        "role": "user", 
        "content": f"{question}\n\n[SYSTEM COMMAND: 1. Answer in the exact same language as the question above. 2. Use ONLY the provided context. If not in context, say you don't know.]"
    })

    # 5. Appel à Ollama (API Chat)
    ollama_url = "http://localhost:11434/api/chat"
    payload = {
        "model": "gemma2",  # (Ou le modèle léger de ton choix)
        "messages": messages,
        "stream": False,
        # "options": {
        #     "num_thread": 4,
        #     "num_predict": 250, 
        #     "num_ctx": 3000,     # Assez grand pour garder l'historique en mémoire
        #     "temperature": 0.1   # Très bas pour qu'elle reste factuelle (zéro invention)
        # }
    }
    
    try:
        response = requests.post(ollama_url, json=payload)
        
        if response.status_code != 200:
            erreur_detail = response.text 
            return f"🚨 Ollama a planté (Erreur {response.status_code}) : {erreur_detail}"
        
        full_response = response.json()["message"]["content"]
        
        if "</think>" in full_response:
            final_answer = full_response.split("</think>")[-1].strip()
            return final_answer
            
        return full_response.strip()

    except requests.exceptions.ConnectionError:
        return "🚨 Erreur : Ollama n'est pas en cours d'exécution sur votre machine."

# def ask_chatbot(question, history=[]):
#     if vector_db.ntotal == 0:
#         return "Please upload a document first to build the database."

#     # 1. Search FAISS using the new question
#     question_vector = embedder.encode([question])
#     distances, indices = vector_db.search(np.array(question_vector), k=3)
    
#     retrieved_chunks = []
#     for faiss_id in indices[0]:
#         if faiss_id != -1:
#             try:
#                 chunk = DocumentChunk.objects.get(faiss_index_id=faiss_id)
#                 retrieved_chunks.append(chunk.text_content)
#             except DocumentChunk.DoesNotExist:
#                 continue
#     context = "\n\n".join(retrieved_chunks)
    
#     # 2. Build the dynamic SYSTEM prompt
#     system_instruction = f"""You are a highly intelligent and helpful AI assistant. 
#     Use the following context to answer the user's questions. 
    
#     CRITICAL RULES:
#     1. Answer in the EXACT SAME LANGUAGE that the user uses to ask the question.
#     2. Write in clear, complete, and grammatically correct sentences. 
#     3. If the context contains formatting errors or joined words, fix them mentally and output perfectly spaced words.
#     4. Do not just quote Table of Contents lines or page numbers. Explain the actual answer.
    
#     Context from documents:
#     {context}
#     """

#     # 3. Format the messages for Ollama's /api/chat endpoint
#     messages =[
#         {"role": "system", "content": system_instruction}
#     ]
    
#     # Add the previous conversation history so the AI "remembers"
#     for msg in history:
#         messages.append({"role": msg["role"], "content": msg["content"]})
        
#     # Add the current question
#     messages.append({"role": "user", "content": question})

#     # 4. Call Ollama's CHAT endpoint (not generate)
#     ollama_url = "http://localhost:11434/api/chat"
    
#     payload = {
#         "model": "gemma2", # Or your preferred model
#         "messages": messages,    # We send the ARRAY of messages, not a single prompt string
#         "stream": False,
#         # "options": {
#         #     "num_thread": 4,
#         #     "num_predict": 250, 
#         #     "num_ctx": 3000,     # Increased slightly so it can remember the history!
#         #     "temperature": 0.2
#         # }
#     }
    
#     try:
#         response = requests.post(ollama_url, json=payload)
#         response.raise_for_status() 
        
#         # The response format for /api/chat is slightly different
#         full_response = response.json()["message"]["content"]
        
#         # Clean thinking tags if using a reasoning model
#         if "</think>" in full_response:
#             final_answer = full_response.split("</think>")[-1].strip()
#             return final_answer
            
#         return full_response.strip()

#     except requests.exceptions.ConnectionError:
#         return "🚨 Error: Ollama is not running."

# def ask_chatbot(question):
#     if vector_db.ntotal == 0:
#         return "Je n'ai pas encore de documents dans ma base de données. Veuillez d'abord uploader un fichier."

#     # 1. Embed the user's question
#     question_vector = embedder.encode([question])
#     distances, indices = vector_db.search(np.array(question_vector), k=3)
    
#     # 2. Retrieve the text from Django Database
#     retrieved_chunks = []
#     for faiss_id in indices[0]:
#         if faiss_id != -1:
#             try:
#                 chunk = DocumentChunk.objects.get(faiss_index_id=faiss_id)
#                 retrieved_chunks.append(chunk.text_content)
#             except DocumentChunk.DoesNotExist:
#                 continue
#     context = "\n\n".join(retrieved_chunks)
    
#     # 3. Create a clean Prompt
#     prompt = f"""Tu es un assistant IA professionnel. Réponds à la question en utilisant UNIQUEMENT le contexte fourni ci-dessous. Ne rajoute pas d'informations extérieures.
    
# Contexte: 
# {context}

# Question: {question}
# """

#     # 4. Send to local Ollama DeepSeek API
#     ollama_url = "http://localhost:11434/api/generate"
#     payload = {
#         "model": "gemma2", # The model
#         "prompt": prompt,
#         "stream": False # Tells Ollama to wait and send the complete answer at once
#     }
    
#     try:
#         response = requests.post(ollama_url, json=payload)
#         response.raise_for_status() 
        
#         # Removes the thinking tags so the user only sees the final answer.
#         full_response = response.json()["response"]
#         if "</think>" in full_response:
#             final_answer = full_response.split("</think>")[-1].strip()
#             return final_answer
#         return full_response.strip()

#     except requests.exceptions.ConnectionError:
#         return "🚨 Erreur : Ollama n'est pas en cours d'exécution. Veuillez vérifier que l'application Ollama est ouverte sur votre ordinateur."
    
def clear_database():
    """Clears the SQLite Database, FAISS RAM index, and FAISS disk file."""
    try:
        # 1. Delete all text from the Django Database
        Document.objects.all().delete()
        
        # 2. Clear the FAISS index currently running in RAM
        vector_db.reset()
        
        # 3. Overwrite the FAISS file on your hard drive with the empty index
        faiss.write_index(vector_db, FAISS_INDEX_PATH)
        
        return True
    except Exception as e:
        print(f"Error clearing database: {e}")
        return False