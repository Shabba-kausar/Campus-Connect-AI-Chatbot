from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),   # chatbot UI
    path('process_message/', views.process_message, name='process_message'),  # API
]
