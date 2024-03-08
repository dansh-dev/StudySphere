from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.chat_index, name='chat_index'),
    path('chat_room/<str:room_name>/', views.room, name='chat_room'),
    path('new_chat_room/', views.new_chat_room, name='new_chat_room'),
    # other URL patterns...


]