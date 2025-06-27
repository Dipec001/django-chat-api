from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from chat.models import Message, FriendRequest
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatAPITests(APITestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(email="user1@example.com", password="testpass")
        self.user2 = User.objects.create_user(email="user2@example.com", password="testpass")
        self.user3 = User.objects.create_user(email="user3@example.com", password="testpass")  # not a friend

        # Authenticate user1
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

        # Create accepted friend between user1 and user2
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2, status="accepted")

        # Create some messages
        self.message1 = Message.objects.create(sender=self.user1, receiver=self.user2, content="Hi")
        self.message2 = Message.objects.create(sender=self.user2, receiver=self.user1, content="Hello back")

    def test_send_message_to_friend(self):
        url = reverse('send-message')
        data = {
            "receiver": self.user2.id,
            "content": "How are you?",
            "message_type": "text"
        }
        response = self.client.post(url, data)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_201_CREATED)
        self.assertEqual(json_response["data"]["content"], "How are you?")

    def test_send_message_to_non_friend_should_fail(self):
        url = reverse('send-message')
        data = {
            "receiver": self.user3.id,
            "content": "Hey stranger",
        }
        response = self.client.post(url, data)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_403_FORBIDDEN)

    def test_get_chat_inbox_should_return_latest_message_per_friend(self):
        url = reverse('chat-inbox')
        response = self.client.get(url)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_200_OK)
        self.assertGreaterEqual(len(json_response["data"]["results"]), 1)

    def test_get_chat_inbox_with_no_messages_should_return_empty(self):
        # Clear messages
        Message.objects.all().delete()
        url = reverse('chat-inbox')
        response = self.client.get(url)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_200_OK)
        self.assertEqual(json_response["data"]["results"], [])