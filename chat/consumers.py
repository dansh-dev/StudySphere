import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatMessage, ChatRoom
from asgiref.sync import sync_to_async  # Import sync_to_async
from django.contrib.auth import get_user_model

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user_id = self.scope['user'].id

        # Save message to database using sync_to_async
        room = await sync_to_async(ChatRoom.objects.get)(name=self.room_name)
        user = await sync_to_async(get_user_model().objects.get)(id=user_id)
        await sync_to_async(ChatMessage.objects.create)(room=room, user=user, message=message)

        # Broadcast message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': user.username
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': f'{username}: {message}'
        }))