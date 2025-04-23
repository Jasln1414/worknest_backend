from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
import json
from datetime import datetime
from user_account.models import Candidate, Employer
from chat.models import ChatMessage, ChatRoom
from django.contrib.auth import get_user_model


from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
import json
from datetime import datetime
from user_account.models import Candidate, Employer
from chat.models import ChatMessage, ChatRoom
from django.contrib.auth import get_user_model


class ChatConsumer(AsyncJsonWebsocketConsumer):
    active_users = set()
    online_users = set()

    async def connect(self):
        self.candidate_id = self.scope['url_route']['kwargs']['candidate_id']
        self.employer_id = self.scope['url_route']['kwargs']['employer_id']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.chat_room_name = f'chat_{self.candidate_id}_{self.employer_id}'

        self.candidate = await self.get_candidate_instance(self.candidate_id)
        self.employer = await self.get_employer_instance(self.employer_id)
        if not self.candidate or not self.employer:
            await self.close()
            return

        await self.channel_layer.group_add(self.chat_room_name, self.channel_name)
        ChatConsumer.active_users.add(str(self.user_id))
        ChatConsumer.online_users.add(str(self.user_id))
        await self.notify_online_status_update()
        await self.notify_active_users_update()
        await self.accept()

        existing_messages = await self.get_existing_messages()
        for message in existing_messages:
            await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def get_existing_messages(self):
        chatroom, _ = ChatRoom.objects.get_or_create(candidate=self.candidate, employer=self.employer)
        messages = ChatMessage.objects.filter(chatroom=chatroom).order_by('timestamp')
        return [{
            'message': m.message,
            'sendername': m.sendername,
            'is_read': m.is_read,
            'timestamp': m.timestamp.isoformat() if m.timestamp else None
        } for m in messages]

    @database_sync_to_async
    def get_candidate_instance(self, candidate_id):
        try:
            return Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return None

    @database_sync_to_async
    def get_employer_instance(self, employer_id):
        try:
            return Employer.objects.get(id=employer_id)
        except Employer.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat_room_name, self.channel_name)
        if hasattr(self, 'user_id'):
            ChatConsumer.active_users.discard(str(self.user_id))
            ChatConsumer.online_users.discard(str(self.user_id))
            await self.notify_online_status_update()
            await self.notify_active_users_update()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'get_active_users':
            await self.send_active_users()
            return
        elif message_type == 'get_online_users':
            await self.send_online_users()
            return
        elif message_type == 'set_status':
            status = data.get('status')
            if status == 'online':
                ChatConsumer.online_users.add(str(self.user_id))
            elif status == 'offline':
                ChatConsumer.online_users.discard(str(self.user_id))
            await self.notify_online_status_update()
            return

        message = data.get('message')
        if not message:
            await self.send(text_data=json.dumps({'error': 'Message content is required'}))
            return

        sendername = data.get('sendername', 'Anonymous')
        sender_id = data.get('sender_id')
        timestamp = datetime.now().isoformat()
        
        # Determine recipient
        recipient_id = self.employer_id if str(sender_id) == str(self.candidate_id) else self.candidate_id
        is_read = str(recipient_id) in ChatConsumer.active_users

        await self.save_message(sendername, message, is_read)
        await self.send_notification(recipient_id, sendername, message, sender_id)

        await self.channel_layer.group_send(
            self.chat_room_name,
            {
                'type': 'chat_message',
                'data': {'message': message, 'sendername': sendername, 'is_read': is_read, 'timestamp': timestamp}
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['data']))

    async def send_active_users(self):
        await self.send(text_data=json.dumps({'type': 'active_users', 'users': list(ChatConsumer.active_users)}))
    
    async def send_online_users(self):
        await self.send(text_data=json.dumps({'type': 'online_users', 'users': list(ChatConsumer.online_users)}))

    async def notify_active_users_update(self):
        await self.channel_layer.group_send(
            self.chat_room_name,
            {'type': 'active_users_update', 'users': list(ChatConsumer.active_users)}
        )
    
    async def notify_online_status_update(self):
        await self.channel_layer.group_send(
            self.chat_room_name,
            {'type': 'online_status_update', 'online_users': list(ChatConsumer.online_users)}
        )

    async def active_users_update(self, event):
        await self.send(text_data=json.dumps({'type': 'active_users', 'users': event['users']}))
    
    async def online_status_update(self, event):
        await self.send(text_data=json.dumps({'type': 'online_users', 'users': event['online_users']}))

    @database_sync_to_async
    def save_message(self, sendername, message, is_read):
        chatroom, _ = ChatRoom.objects.get_or_create(candidate=self.candidate, employer=self.employer)
        ChatMessage.objects.create(chatroom=chatroom, message=message, sendername=sendername, is_read=is_read)

    async def send_notification(self, recipient_id, sendername, message, sender_id):
        if not recipient_id or recipient_id == '0' or str(recipient_id) == str(self.user_id):
            return
        
        try:
            unread_count = await self.get_unread_count(recipient_id)
            await self.channel_layer.group_send(
                f'notification_{recipient_id}',
                {
                    'type': 'notify_message',
                    'message': {
                        'text': f"New message from {sendername}: {message}",
                        'sender': sendername,
                        'sender_id': sender_id,
                        'is_read': False,
                        'timestamp': datetime.now().isoformat(),
                        'chat_id': self.chat_room_name
                    },
                    'unread_count': unread_count
                }
            )
        except Exception as e:
            print(f"Error sending notification: {str(e)}")

    @database_sync_to_async
    def get_unread_count(self, user_id):
        try:
            User = get_user_model()
            user = User.objects.get(id=user_id)
            try:
                candidate = Candidate.objects.get(user=user)
                chatrooms = ChatRoom.objects.filter(candidate=candidate)
            except Candidate.DoesNotExist:
                employer = Employer.objects.get(user=user)
                chatrooms = ChatRoom.objects.filter(employer=employer)
            return ChatMessage.objects.filter(
                chatroom__in=chatrooms,
                is_read=False
            ).exclude(sendername=user.get_username()).count()
        except User.DoesNotExist:
            print(f"User with ID {user_id} does not exist.")
            return 0
        except Exception as e:
            print(f"Error in get_unread_count: {str(e)}")
            return 0


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.notification_group_name = f'notification_{self.user_id}'
        await self.channel_layer.group_add(self.notification_group_name, self.channel_name)
        await self.accept()

        unread_count = await self.get_unread_notifications_count()
        print(f"Initial unread count for user {self.user_id}: {unread_count}")
        await self.send(text_data=json.dumps({'type': 'initial_count', 'unread_count': unread_count}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.notification_group_name, self.channel_name)

    async def notify_message(self, event):
        message = event['message']
        sender_id = message.get('sender_id')
        
        # Skip if the sender is the same as the recipient
        if str(sender_id) == str(self.user_id):
            return
        
        print(f"Sending notification to user {self.user_id}: {message}")
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message,
            'unread_count': event['unread_count']
        }))

    @database_sync_to_async
    def get_unread_notifications_count(self):
        try:
            User = get_user_model()
            
            user = User.objects.get(id=self.user_id)
            try:
                candidate = Candidate.objects.get(user=user)
                chatrooms = ChatRoom.objects.filter(candidate=candidate)
            except Candidate.DoesNotExist:
                employer = Employer.objects.get(user=user)
                chatrooms = ChatRoom.objects.filter(employer=employer)
            return ChatMessage.objects.filter(
                chatroom__in=chatrooms,
                is_read=False
            ).exclude(sendername=user.get_username()).count()
        except User.DoesNotExist:
            print(f"User with ID {self.user_id} does not exist.")
            return 0
        except Exception as e:
            print(f"Error in get_unread_notifications_count: {str(e)}")
            return 0