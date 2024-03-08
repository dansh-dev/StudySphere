from django.shortcuts import render, redirect
from .models import ChatRoom, ChatMessage

import re
from django.utils.text import slugify

# This is the homepage of the chat module where users can view all chatrooms
def chat_index(request):
    if request.user.is_authenticated:
        # Retrieves all rooms from DB
        chatrooms = ChatRoom.objects.all()
        # Returns them
        return render(request, 'chat_index.html', {'chatrooms': chatrooms})
    else: 
        return redirect('/courses/not_authorized')

# This defines the /room view which is accessed when a user is viewing a chat
def room(request, room_name):
    if request.user.is_authenticated: 
        # Retrieves all relevant messages and renders them
        room_messages = ChatMessage.objects.filter(room__name=room_name).order_by('timestamp')
        return render(request, 'room.html', {'room_name': room_name, 'room_messages': room_messages})
    else: 
        return redirect('/courses/not_authorized')

# This defines the view for the creation of a chat room
def new_chat_room(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            room_name = request.POST.get('room_name')
            # Validation of room name
            room_name = re.sub(r'\s+', '_', room_name)  # Replace spaces with underscores
            room_name = re.sub(r'[^a-zA-Z0-9_-]', '', room_name)  # Remove invalid characters
            room_slug = slugify(room_name)
            chat_room = ChatRoom.objects.create(name=room_slug)
            
            return redirect('chat_room', room_name=room_slug)
        return render(request, 'new_chat_room.html')
    else: 
        return redirect('/courses/not_authorized')