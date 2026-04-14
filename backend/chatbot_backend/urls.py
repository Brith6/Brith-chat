from django.contrib import admin
from django.urls import path
from core.views import UploadDocumentView, ChatbotQueryView, ClearDatabaseView

urlpatterns =[
    path('admin/', admin.site.urls),
    path('api/upload/', UploadDocumentView.as_view(), name='upload_doc'),
    path('api/chat/', ChatbotQueryView.as_view(), name='chat'),
    path('api/clear/', ClearDatabaseView.as_view(), name='clear_db'),
]