# Local RAG Chatbot (Django + Streamlit + Ollama)

This project is a local document-question answering chatbot:

- Backend API: Django + Django REST Framework
- Retrieval: FAISS + Sentence Transformers embeddings
- OCR/PDF extraction: Tesseract + Pillow + PyPDF2
- UI: Streamlit
- LLM inference: Ollama (local model, currently set to gemma2)

## Project Structure

- backend/: Django project and Streamlit frontend
- backend/core/ai_services.py: document processing, embeddings, FAISS, Ollama call
- backend/frontend.py: Streamlit chat interface

## Prerequisites

1. Python 3.10 or newer
2. Ollama installed and running
3. Tesseract OCR installed on your system

### Install Tesseract

Ubuntu/Debian:

   sudo apt update
   sudo apt install -y tesseract-ocr

macOS (Homebrew):

   brew install tesseract

Windows:

- Install Tesseract from the official installer, then add it to PATH.

## Quick Start

From the project root:

1. Create and activate a virtual environment

Linux/macOS:

   python3 -m venv .venv
   source .venv/bin/activate

Windows PowerShell:

   py -m venv .venv
   .venv\Scripts\Activate.ps1

2. Install Python dependencies

   pip install --upgrade pip
   pip install django djangorestframework streamlit requests numpy pillow pytesseract PyPDF2 sentence-transformers faiss-cpu

3. Run database migrations

   cd backend
   python manage.py migrate

4. Pull and run the Ollama model used by this project

   ollama pull gemma2

You can keep Ollama running in another terminal with:

   ollama run gemma2

## Run the Application

Use 2 terminals (with the same virtual environment activated).

Terminal 1, Django API:

   cd backend
   python manage.py runserver

Terminal 2, Streamlit UI:

   streamlit run backend/frontend.py

Then open the Streamlit URL shown in terminal (usually http://localhost:8501).

## How to Use

1. Upload a PDF/JPG/PNG from the sidebar.
2. Wait for indexing to complete.
3. Ask questions in the chat box.
4. Use the clear button to reset indexed data.

## API Endpoints (Django)

- POST /api/upload/
- POST /api/chat/
- POST /api/clear/

Default backend URL used by Streamlit: http://127.0.0.1:8000

## Run Tests

From backend directory:

   python manage.py test core

## Notes and Troubleshooting

- If you see connection errors in Streamlit, verify Django is running on port 8000.
- If OCR on images fails, verify Tesseract is correctly installed and available in PATH.
- If LLM replies fail, verify Ollama is running and gemma2 is available.