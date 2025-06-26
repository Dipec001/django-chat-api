from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from chat.serializers.friend_serializers import FriendRequestSerializer
from chat.models import FriendRequest, UserProfile
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from chat.utils import get_friends
from chat.serializers.friend_serializers import UserSearchResultSerializer
from drf_yasg import openapi

class SendFriendRequestView(APIView):
    """
    Send a friend request to another user.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Send friend request",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['to_user'],
            properties={
                'to_user': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID to send request to')
            }
        ),
        responses={201: "Created", 400: "Invalid request"}
    )
    def post(self, request):
        to_user = request.data.get("to_user")
        if to_user == request.user.id:
            return Response({"error": "Cannot send request to yourself."}, status=400)
        if FriendRequest.objects.filter(from_user=request.user, to_user_id=to_user).exists():
            return Response({"error": "Request already sent."}, status=400)

        serializer = FriendRequestSerializer(data={"to_user": to_user})
        if serializer.is_valid():
            serializer.save(from_user=request.user)
            return Response({
                "success": True,
                "message": "Friend request sent."
            }, status=201)
        return Response(serializer.errors, status=400)


class AcceptFriendRequestView(APIView):
    """
    Accept a pending friend request.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Accept friend request")
    def post(self, request, pk):
        try:
            fr = FriendRequest.objects.get(id=pk, to_user=request.user, status='pending')
            fr.status = 'accepted'
            fr.save()
            return Response({"success": "Friend request accepted."})
        except FriendRequest.DoesNotExist:
            return Response({"error": "Request not found."}, status=404)


class DeclineFriendRequestView(APIView):
    """
    Decline a pending friend request.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Decline friend request")
    def post(self, request, pk):
        try:
            fr = FriendRequest.objects.get(id=pk, to_user=request.user, status='pending')
            fr.status = 'declined'
            fr.save()
            return Response({"success": "Friend request declined."})
        except FriendRequest.DoesNotExist:
            return Response({"error": "Request not found."}, status=404)


class RemoveFriendView(APIView):
    """
    Remove an existing friend.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Remove a friend",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID of the friend to remove')
            }
        ),
        responses={200: "Success"}
    )
    def post(self, request):
        user_id = request.data.get("user_id")
        deleted, _ = FriendRequest.objects.filter(
            (Q(from_user=request.user, to_user_id=user_id) |
             Q(from_user_id=user_id, to_user=request.user)),
            status='accepted'
        ).delete()

        return Response({"success": "Friend removed." if deleted else "No such friend found."})


class FriendListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="List friends")
    def get(self, request):
        friends = get_friends(request.user)
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(friends, request)
        serializer = UserSearchResultSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PendingFriendRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="List pending incoming requests")
    def get(self, request):
        pending = FriendRequest.objects.filter(to_user=request.user, status='pending').order_by('-created_at')
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(pending, request)
        serializer = FriendRequestSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SearchUsersView(APIView):
    """
    Search users by username or full name.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Search users",
        manual_parameters=[
            openapi.Parameter(
                'q', openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description="Username or full name to search for"
            )
        ]
    )
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({"error": "Query parameter `q` is required."}, status=400)

        profiles = UserProfile.objects.filter(
            Q(username__icontains=query) | Q(full_name__icontains=query)
        ).exclude(user=request.user).order_by("username")

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(profiles, request)
        serializer = UserSearchResultSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

