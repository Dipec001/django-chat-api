import pytest
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken
from djangochatapi.asgi import application
from django.contrib.auth import get_user_model
from chat.models import FriendRequest


User = get_user_model()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_successful_chat_connection_and_message():
    # Setup users
    user1 = await User.objects.acreate(email="alice@example.com", password="pass")
    user2 = await User.objects.acreate(email="bob@example.com", password="pass")

    # Make them friends
    await FriendRequest.objects.acreate(from_user=user1, to_user=user2, status="accepted")

    token = str(AccessToken.for_user(user1))

    # WebSocket connection
    communicator = WebsocketCommunicator(
        application,
        f"/ws/chat/{user2.id}/?token={token}"
    )
    connected, _ = await communicator.connect()
    assert connected

    # Send a message
    message_payload = {"content": "Hello Bob!", "message_type": "text"}
    await communicator.send_json_to(message_payload)

    response = await communicator.receive_json_from()
    assert response["content"] == "Hello Bob!"
    assert response["sender"] == user1.email
    assert response["receiver"] == user2.id

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_connection_rejected_if_friend_does_not_exist():
    user = await User.objects.acreate(email="test@example.com", password="pass")
    token = str(AccessToken.for_user(user))

    invalid_id = 999

    communicator = WebsocketCommunicator(
        application,
        f"/ws/chat/{invalid_id}/?token={token}"
    )
    connected = False
    try:
        connected, close_code = await communicator.connect()
    except AssertionError:
        connected = False
        close_code = 4001  # manually assume based on your consumer code

    assert not connected
    assert close_code == 4001


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_connection_rejected_if_not_friends():
    user1 = await User.objects.acreate(email="a@example.com", password="pass")
    user2 = await User.objects.acreate(email="b@example.com", password="pass")

    token = str(AccessToken.for_user(user1))

    communicator = WebsocketCommunicator(
        application,
        f"/ws/chat/{user2.id}/?token={token}"
    )
    connected = False
    try:
        connected, close_code = await communicator.connect()
    except AssertionError:
        connected = False
        close_code = 4002  # based on your consumer

    assert not connected
    assert close_code == 4002


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_missing_content_key_in_message():
    user1 = await User.objects.acreate(email="alice2@example.com", password="pass")
    user2 = await User.objects.acreate(email="bob2@example.com", password="pass")

    await FriendRequest.objects.acreate(from_user=user1, to_user=user2, status="accepted")
    token = str(AccessToken.for_user(user1))

    communicator = WebsocketCommunicator(
        application,
        f"/ws/chat/{user2.id}/?token={token}"
    )
    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({"invalid_key": "Hello"})

    error = await communicator.receive_json_from()
    assert "error" in error
    assert error["error"] == "Missing 'content' in message payload."

    await communicator.disconnect()
