import pytest
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken
from djangochatapi.asgi import application
from chat.models import Group, GroupMembership
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_group_websocket_connection():
    # Create user and group
    user = await User.objects.acreate(email="user@example.com", password="pass")
    group = await Group.objects.acreate(name="Test Group", creator=user)
    await GroupMembership.objects.acreate(user=user, group=group)

    # Generate JWT token
    token = str(AccessToken.for_user(user))

    # Simulate WebSocket connection
    communicator = WebsocketCommunicator(
        application,
        f"/ws/group/{group.id}/?token={token}"
    )
    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({"content": "Hello Test Group!"})
    response = await communicator.receive_json_from()

    assert response["content"] == "Hello Test Group!"
    assert response["sender"] == user.email

    await communicator.disconnect()
