from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.user_data = {
            'email': 'user@example.com',
            'password': 'stringst',
            'username': 'testuser',
            'full_name': 'Full Name'
        }
        
    def test_register_user_successfully(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(hasattr(user, 'profile'))  # ✅ Profile was created

    def test_register_user_with_short_password(self):
        data = self.user_data.copy()
        data['password'] = 'short'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_register_user_with_no_password(self):
        data = self.user_data.copy()
        data['password'] = ''
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_no_email(self):
        data = self.user_data.copy()
        data['email'] = ''
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_no_username(self):
        data = self.user_data.copy()
        data['username'] = ''
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_no_full_name(self):
        data = self.user_data.copy()
        data['full_name'] = ''
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_existing_email(self):
        self.client.post(self.register_url, self.user_data, format='json')
        data = self.user_data.copy()
        data['username'] = 'anotherusername'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_existing_username(self):
        self.client.post(self.register_url, self.user_data, format='json')
        data = self.user_data.copy()
        data['email'] = 'another@example.com'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_valid_credentials(self):
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
        }
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertIn('access', json_response['data'])
        self.assertIn('refresh', json_response['data'])
        self.assertEqual(json_response['data']['user']['email'], data['email'])

    def test_login_with_invalid_password(self):
        data = {
            'email': self.user_data['email'],
            'password': 'wrongpassword',
        }
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_unregistered_email(self):
        data = {
            'email': 'notexist@example.com',
            'password': 'stringst',
        }
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
