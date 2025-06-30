import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from chat.models import Message, Group, GroupMessage, GroupMembership, FriendRequest
from django.db.models import Q
import logging
from prometheus_client import Counter, Gauge

active_connections = Gauge("websocket_connections_active", "Current active WebSocket connections")
private_msg_counter = Counter("private_messages_total", "Total private messages")
group_msg_counter = Counter("group_messages_total", "Total group messages")
messages_sent = Counter("chat_messages_sent_total", "Total number of messages sent")
websocket_errors = Counter("websocket_errors_total", "Total WebSocket errors")


logger = logging.getLogger('chat')

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.friend_id = self.scope["url_route"]["kwargs"]["friend_id"]

        self.friend = await self.get_user_by_id(self.friend_id)

        if not self.friend:
            await self.send_json_error("The user you're trying to chat with does not exist.")
            await self.close(4001)
            return

        is_friend = await self.are_users_friends(self.user, self.friend)
        if not is_friend:
            await self.send_json_error("You can only chat with users you're friends with.")
            await self.close(4002)
            return

        self.room_name = f"chat_{min(self.user.id, self.friend.id)}_{max(self.user.id, self.friend.id)}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        active_connections.inc()

        logger.info(f"[WS CONNECT] {self.user} connected to room {self.room_name}")


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

        active_connections.dec()

        logger.info(f"[WS DISCONNECT] {self.user} disconnected from room {self.room_name}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            content = data["content"]
            message_type = data.get("message_type", "text")

            message = await database_sync_to_async(Message.objects.create)(
                sender=self.user,
                receiver=self.friend,
                content=content,
                message_type=message_type,
            )
            logger.info(f"[MESSAGE SENT] {self.user} → {self.friend}: {content}")

            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "chat_message",
                    "message": {
                        "id": message.id,
                        "sender": self.user.email,
                        "receiver": self.friend.id,
                        "content": message.content,
                        "message_type": message.message_type,
                        "created_at": str(message.created_at),
                    }
                }
            )
            private_msg_counter.inc()
            messages_sent.inc() # Promotheus

        except KeyError:
            websocket_errors.inc()
            logger.warning(f"[KEY ERROR] Message payload missing 'content' by {self.user}")
            await self.send_json_error("Missing 'content' in message payload.")
        except Exception as e:
            websocket_errors.inc()
            logger.error(f"[EXCEPTION] Error in message receive by {self.user}: {str(e)}", exc_info=True)
            await self.send_json_error(f"Unexpected error: {str(e)}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def send_json_error(self, message):
        await self.send(text_data=json.dumps({"error": message}))

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def are_users_friends(self, user1, user2):
        return FriendRequest.objects.filter(
            Q(from_user=user1, to_user=user2) | Q(from_user=user2, to_user=user1),
            status="accepted"
        ).exists()


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]
        self.room_name = f"group_{self.group_id}"

        # Check if group exists
        self.group = await self.get_group_or_none(self.group_id)
        if not self.group:
            await self.close(code=4001)
            return

        # Check membership
        is_member = await self.is_group_member(self.group_id, self.user)
        if not is_member:
            await self.send(json.dumps({"error": "You are not a member of this group."}))
            await self.close(code=4002)
            return

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
        logger.info(f"[WS CONNECT] {self.user} joined group room {self.room_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)
        logger.info(f"[WS DISCONNECT] {self.user} left group room {self.room_name}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            content = data.get("content")
            message_type = data.get("message_type", "text")

            if not content:
                await self.send(json.dumps({"error": "Message content is required."}))
                return

            if len(content) > 1000:
                await self.send(json.dumps({"error": "Message too long (max 1000 characters)."}))
                return

            msg = await database_sync_to_async(GroupMessage.objects.create)(
                group=self.group,
                sender=self.user,
                content=content,
                message_type=message_type,
            )

            logger.info(f"[GROUP MESSAGE SENT] {self.user} → Group {self.group_id}: {content}")

            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "group_message",
                    "message": {
                        "id": msg.id,
                        "sender": self.user.email,
                        "group": self.group_id,
                        "content": msg.content,
                        "message_type": msg.message_type,
                        "created_at": str(msg.created_at),
                    }
                }
            )
            group_msg_counter.inc()
            messages_sent.inc() # Promotheus

        except Exception as e:
            websocket_errors.inc()
            logger.error(f"[GROUP EXCEPTION] {self.user} → Group {self.group_id}: {str(e)}", exc_info=True)
            await self.send(json.dumps({"error": f"An error occurred: {str(e)}"}))

    async def group_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def is_group_member(self, group_id, user):
        return GroupMembership.objects.filter(group_id=group_id, user=user).exists()

    @database_sync_to_async
    def get_group_or_none(self, group_id):
        try:
            return Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return None
