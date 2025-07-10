from django.urls import path
from . import views





urlpatterns = [
  
    path('', views.index, name="index"),
    path('api/message/', views.process_message, name="process_message"),
]
