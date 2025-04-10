import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from .models import Message, Conversation

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

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

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        
        # Save message to database
        message_obj = await self.save_message(message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": message_obj["id"],
                    "content": message_obj["content"],
                    "message_type": message_obj["message_type"],
                    "sender_id": message_obj["sender_id"],
                    "created_at": message_obj["created_at"],
                    "image_url": message_obj.get("image_url"),
                    "voice_url": message_obj.get("voice_url")
                }
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "message": message
        }))
        
    @sync_to_async
    def save_message(self, message_data):
        conversation = Conversation.objects.get(id=self.conversation_id)
        sender = self.scope["user"]
        
        # Create message
        message_obj = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=message_data.get('content', ''),
            message_type=message_data.get('message_type', 'text'),
            image=message_data.get('image'),
            voice=message_data.get('voice')
        )
        
        return {
            'id': message_obj.id,
            'sender_id': sender.id,
            'content': message_obj.content,
            'message_type': message_obj.message_type,
            'created_at': message_obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'image_url': message_obj.image.url if message_obj.image else None,
            'voice_url': message_obj.voice.url if message_obj.voice else None
        } 