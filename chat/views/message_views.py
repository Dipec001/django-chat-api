from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from chat.models import Message
from chat.serializers import MessageSerializer
from chat.utils import are_friends, get_friend_ids
from rest_framework.pagination import PageNumberPagination
from django.db.models import Max, Q
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth import get_user_model

User = get_user_model()

class SendMessageView(APIView):
    """
    Send a message to a friend.
    Requires: receiver ID, content.
    Sender is set as the logged-in user.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Send a message to a friend",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["receiver", "content"],
            properties={
                "receiver": openapi.Schema(type=openapi.TYPE_INTEGER, description="User ID of the receiver"),
                "content": openapi.Schema(type=openapi.TYPE_STRING, description="Message content"),
                "message_type": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["text", "image", "file"],
                    default="text",
                    description="Type of message"
                ),
            }
        )
    )
    def post(self, request):
        receiver_id = request.data.get("receiver")
        if not receiver_id:
            return Response({"error": "Receiver is required"}, status=400)

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if not are_friends(request.user, receiver):
            return Response({"error": "You can only message accepted friends."}, status=403)

        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)


class ChatHistoryView(generics.ListAPIView):
    """
    Get chat history with a specific friend.
    Marks unread messages as read.
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        other_user_id = self.kwargs.get("id")
        other_user = User.objects.filter(id=other_user_id).first()

        if not other_user or not are_friends(self.request.user, other_user):
            return Message.objects.none()

        # Mark received messages as read
        Message.objects.filter(
            sender=other_user,
            receiver=self.request.user,
            is_read=False
        ).update(is_read=True)

        return Message.objects.filter(
            sender__in=[self.request.user, other_user],
            receiver__in=[self.request.user, other_user]
        ).order_by("-created_at")

    @swagger_auto_schema(operation_summary="View chat history with a friend")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# class ChatInboxView(APIView):
#     """
#     Get latest message from each friend (chat inbox).
#     Only includes accepted friends.
#     """

#     permission_classes = [permissions.IsAuthenticated]

#     @swagger_auto_schema(operation_summary="Get latest messages from each friend")
#     def get(self, request):
#         user = request.user
#         friend_ids = get_friend_ids(user)

#         # Get latest message between user and each friend
#         latest_ids = (
#             Message.objects
#             .filter(
#                 Q(sender=user, receiver__in=friend_ids) |
#                 Q(receiver=user, sender__in=friend_ids)
#             )
#             .values('sender', 'receiver')
#             .annotate(latest_id=Max('id'))
#             .values_list('latest_id', flat=True)
#         )

#         # Fetch the actual message objects and serialize
#         messages = Message.objects.filter(id__in=latest_ids).order_by('-created_at')
#         serializer = MessageSerializer(messages, many=True)
#         return Response(serializer.data)


class ChatInboxView(APIView):
    """
    Get latest message from each friend (chat inbox).
    Only includes accepted friends.
    Only one latest message per unique friend, regardless of who sent it.
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Get latest messages from each friend")
    def get(self, request):
        user = request.user
        friend_ids = get_friend_ids(user)

        # Step 1: Get latest message IDs between user and each friend
        latest_ids = (
            Message.objects
            .filter(
                Q(sender=user, receiver__in=friend_ids) |
                Q(receiver=user, sender__in=friend_ids)
            )
            .values('sender', 'receiver')
            .annotate(latest_id=Max('id'))
            .values_list('latest_id', flat=True)
        )

        # Step 2: Fetch those messages and sort them
        messages = Message.objects.filter(id__in=latest_ids).order_by('-created_at')

        # Step 3: Deduplicate by unique friend ID (regardless of direction)
        seen = set()
        filtered = []
        for msg in messages:
            friend_id = msg.receiver.id if msg.sender == user else msg.sender.id
            if friend_id not in seen:
                seen.add(friend_id)
                filtered.append(msg)

        # Step 4: Paginate the filtered result
        paginator = PageNumberPagination()
        paginated_msgs = paginator.paginate_queryset(filtered, request)

        serializer = MessageSerializer(paginated_msgs, many=True)
        return paginator.get_paginated_response(serializer.data)