from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from chat.models import Group, GroupMembership, GroupMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class GroupMessagingTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email="user1@example.com", password="pass1234")
        self.user2 = User.objects.create_user(email="user2@example.com", password="pass1234")
        self.client.login(email="user1@example.com", password="pass1234")

        self.group = Group.objects.create(name="Test Group", description="Test Desc", creator=self.user1)
        GroupMembership.objects.create(group=self.group, user=self.user1)

    def test_create_group(self):
        url = reverse('group-list')
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(url, {"name": "New Group", "description": "Desc"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_group_member(self):
        url = reverse("add-group-member", kwargs={"group_id": self.group.id})
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(url, {"user_id": self.user2.id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(GroupMembership.objects.filter(group=self.group, user=self.user2).exists())

    def test_remove_group_member(self):
        GroupMembership.objects.create(group=self.group, user=self.user2)
        url = reverse("remove-group-member", kwargs={"group_id": self.group.id, "user_id": self.user2.id})
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_send_group_message_as_member(self):
        url = reverse("send-group-message")
        self.client.force_authenticate(user=self.user1)
        data = {"group": self.group.id, "content": "Hello Group!", "message_type": "text"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_send_group_message_as_non_member(self):
        self.client.force_authenticate(user=self.user2)
        url = reverse("send-group-message")
        data = {"group": self.group.id, "content": "Hi", "message_type": "text"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_group_messages_as_member(self):
        GroupMessage.objects.create(group=self.group, sender=self.user1, content="Msg", message_type="text")
        url = reverse("group-messages", kwargs={"group_id": self.group.id})
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_group_messages_as_non_member(self):
        url = reverse("group-messages", kwargs={"group_id": self.group.id})
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_join_group(self):
        url = reverse("join-group", kwargs={"group_id": self.group.id})
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(GroupMembership.objects.filter(group=self.group, user=self.user2).exists())

    def test_search_groups(self):
        url = reverse("search-group") + "?q=Test"
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.json()['data'])
