from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from .ai_services import extract_text_from_file, process_and_store_document, ask_chatbot, clear_database
import os

class UploadDocumentView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided."}, status=400)

        # Save file temporarily
        file_name = default_storage.save(file_obj.name, file_obj)
        file_path = default_storage.path(file_name)
        file_type = file_obj.content_type

        try:
            # 1. Extract text
            text = extract_text_from_file(file_path, file_type)
            
            # 2. Add to Vector DB
            process_and_store_document(text, file_obj.name)
            
            return Response({"message": f"Successfully processed {file_name}. Database updated."})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        finally:
            # Clean up the temporary file
            if os.path.exists(file_path):
                os.remove(file_path)

class ChatbotQueryView(APIView):
    def post(self, request, *args, **kwargs):
        question = request.data.get('question')
        if not question:
            return Response({"error": "No question provided."}, status=400)

        answer = ask_chatbot(question)
        
        return Response({
            "question": question,
            "answer": answer
        })

class ClearDatabaseView(APIView):
    def post(self, request, *args, **kwargs):
        success = clear_database()
        if success:
            return Response({"message": "La base de données a été vidée avec succès."})
        else:
            return Response({"error": "Erreur lors du nettoyage de la base de données."}, status=500)