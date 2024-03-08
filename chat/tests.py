from django.test import TestCase, Client
from django.urls import reverse
from users.models import StudySphereUser

from .models import ChatRoom
import re

# Testing the creation of chat rooms
class NewChatRoomViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = StudySphereUser.objects.create(username='testuser', email='testuser@example.com', password='password')

    # Testing the case where an authed user creates a chat room
    def test_authenticated_user_creates_new_chat_room(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('new_chat_room'), {'room_name': 'Test Room'})
        self.assertEqual(response.status_code, 302)  
        # Verifies the existence of the chat room
        self.assertTrue(ChatRoom.objects.filter(name='test_room').exists())

    # Testing the case where a user would input invalid chars (Should create the room with valid chars)
    def test_room_name_with_spaces_and_special_characters(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('new_chat_room'), {'room_name': 'Test Room!@#'})
        self.assertEqual(response.status_code, 302)  
        self.assertTrue(ChatRoom.objects.filter(name='test_room').exists())

    # Tests the redirect of an unauthed user
    def test_unauthenticated_user_redirected(self):
        response = self.client.get(reverse('new_chat_room'))
        self.assertEqual(response.status_code, 302)
