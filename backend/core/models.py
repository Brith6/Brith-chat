from django.db import models

class Document(models.Model):
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    text_content = models.TextField()
    # This ID tells us exactly which vector in the FAISS database belongs to this text
    faiss_index_id = models.IntegerField(unique=True) 

    def __str__(self):
        return f"Chunk {self.faiss_index_id} of {self.document.file_name}"