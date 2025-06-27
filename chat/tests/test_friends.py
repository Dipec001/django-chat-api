from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from chat.models import FriendRequest, UserProfile

User = get_user_model()

class FriendRequestAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email="user1@example.com", password="pass1234")
        self.user2 = User.objects.create_user(email="user2@example.com", password="pass1234")
        UserProfile.objects.create(user=self.user1, username="user1", full_name="User One")
        UserProfile.objects.create(user=self.user2, username="user2", full_name="User Two")

    def test_send_friend_request(self):
        client = APIClient()
        client.force_authenticate(user=self.user1)

        url = reverse("send-friend-request")
        data = {"to_user": self.user2.id}
        response = client.post(url, data)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_201_CREATED)
        self.assertEqual(json_response["success"], True)
        self.assertEqual(json_response["data"]["message"], "Friend request sent.")

    def test_duplicate_friend_request_blocked(self):
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)

        client = APIClient()
        client.force_authenticate(user=self.user1)

        url = reverse("send-friend-request")
        response = client.post(url, {"to_user": self.user2.id})
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", json_response["errors"])

    def test_accept_friend_request(self):
        FriendRequest.objects.create(from_user=self.user2, to_user=self.user1)
        fr = FriendRequest.objects.get(from_user=self.user2, to_user=self.user1)

        client = APIClient()
        client.force_authenticate(user=self.user1)

        url = reverse("accept-friend-request", args=[fr.id])
        response = client.post(url)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_200_OK)
        self.assertEqual(json_response["data"]["success"], "Friend request accepted.")

    def test_decline_friend_request(self):
        FriendRequest.objects.create(from_user=self.user2, to_user=self.user1)
        fr = FriendRequest.objects.get(from_user=self.user2, to_user=self.user1)

        client = APIClient()
        client.force_authenticate(user=self.user1)

        url = reverse("decline-friend-request", args=[fr.id])
        response = client.post(url)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_200_OK)
        self.assertEqual(json_response["data"]["success"], "Friend request declined.")

    def test_remove_friend(self):
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2, status='accepted')

        client = APIClient()
        client.force_authenticate(user=self.user1)

        url = reverse("remove-friend")
        response = client.post(url, {"user_id": self.user2.id})
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_200_OK)
        self.assertEqual(json_response["data"]["success"], "Friend removed.")

    def test_list_friends(self):
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2, status='accepted')

        client = APIClient()
        client.force_authenticate(user=self.user1)

        url = reverse("friend-list")
        response = client.get(url)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_200_OK)
        self.assertIn("results", json_response["data"])

    def test_pending_requests(self):
        FriendRequest.objects.create(from_user=self.user2, to_user=self.user1, status='pending')

        client = APIClient()
        client.force_authenticate(user=self.user1)

        url = reverse("pending-friend-requests")
        response = client.get(url)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_200_OK)
        self.assertIn("results", json_response["data"])


class UserSearchTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email="user1@example.com", password="pass1234")
        self.user2 = User.objects.create_user(email="user2@example.com", password="pass1234")
        UserProfile.objects.create(user=self.user1, username="divine", full_name="Divine Ekene")
        UserProfile.objects.create(user=self.user2, username="johnny", full_name="Johnny Bravo")

    def test_search_by_username(self):
        client = APIClient()
        client.force_authenticate(user=self.user1)

        url = reverse("user-search") + "?q=joh"
        response = client.get(url)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_200_OK)
        self.assertIn("results", json_response["data"])
        self.assertTrue(any("johnny" in res["username"] for res in json_response["data"]["results"]))

    def test_search_by_full_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user1)

        url = reverse("user-search") + "?q=bravo"
        response = client.get(url)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_200_OK)
        self.assertIn("results", json_response["data"])
        self.assertTrue(any("Johnny" in res["full_name"] for res in json_response["data"]["results"]))

    def test_search_excludes_self(self):
        client = APIClient()
        client.force_authenticate(user=self.user1)

        url = reverse("user-search") + "?q=divine"
        response = client.get(url)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_200_OK)
        self.assertTrue(all(res["user_id"] != self.user1.id for res in json_response["data"]["results"]))

    def test_missing_query_returns_error(self):
        client = APIClient()
        client.force_authenticate(user=self.user1)

        url = reverse("user-search")
        response = client.get(url)
        json_response = response.json()
        self.assertEqual(json_response["status"], status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", json_response["errors"])
