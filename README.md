# Chatbot Project

This project consists of a Django backend integrated with AI services (using Ollama) and a Python-based frontend.

## Prerequisites

- **Python 3.8+**
- **[Ollama](https://ollama.com/)**: Required for local AI model inference.

## Setup Instructions

1. **Set up a Python virtual environment:**
   From the root of the project (`/home/brith/Epitech/chatbot`):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   Make sure to install Django and any required packages (e.g., via `pip install Django requests`). If you have a `requirements.txt`, run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Apply Database Migrations:**
   Navigate to the backend directory and set up the SQLite database:
   ```bash
   cd backend
   python manage.py migrate
   ```

## Running the Project

### 1. Start Ollama
Make sure the Ollama service is running globally and pull your target model (e.g., `llama3` or `mistral`):
```bash
ollama run llama3
```

### 2. Start the Django Backend Server
With your virtual environment activated, navigate to the `backend` directory and start the Django development server:
```bash
cd backend
python manage.py runserver
```

### 3. Start the Frontend
Depending on the library used for `frontend.py` (e.g., Streamlit, Gradio), run the frontend script in a separate terminal:
```bash
# If it's a Streamlit app:
streamlit run backend/frontend.py

# Or if it's a plain Python script:
python backend/frontend.py
```

## How to Test the Project

To run the automated tests for the Django application (which checks the endpoints and AI service integrations), use Django's testing framework.

Ensure you are in the `backend/` directory and your virtual environment is activated:

```bash
cd backend
python manage.py test core
```

This command will automatically discover and run all the test cases defined in `backend/core/tests.py`.