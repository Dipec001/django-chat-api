from rest_framework import generics, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q
from chat.models import Group, GroupMembership, GroupMessage
from chat.serializers import GroupSerializer, GroupMembershipSerializer, GroupMessageSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class GroupViewSet(viewsets.ModelViewSet):
    """
    Group CRUD operations (create, list, retrieve, update, delete).
    Includes only groups the user created or is a member of.
    """
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Group.objects.filter(
            Q(creator=user) | Q(memberships__user=user)
        ).distinct()

    def perform_create(self, serializer):
        group = serializer.save(creator=self.request.user)
        group.memberships.create(user=self.request.user)

    @swagger_auto_schema(operation_summary="List groups the user is part of")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Create a new group")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Retrieve group details")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Update group info")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Delete a group")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class AddGroupMemberView(APIView):
    """
    Add a user to the group (creator only).
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Add member to group",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["user_id"],
            properties={
                "user_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="User ID to add")
            }
        )
    )
    def post(self, request, group_id):
        group = Group.objects.get(id=group_id)

        if group.creator != request.user:
            raise PermissionDenied("Only the group creator can add members.")

        user = User.objects.get(id=request.data["user_id"])
        GroupMembership.objects.get_or_create(group=group, user=user)
        return Response({"detail": f"{user.email} added to group."}, status=200)


class RemoveGroupMemberView(APIView):
    """
    Remove a user from the group (creator only).
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Remove member from group")
    def delete(self, request, group_id, user_id):
        group = Group.objects.get(id=group_id)

        if group.creator != request.user:
            raise PermissionDenied("Only the group creator can remove members.")

        GroupMembership.objects.filter(group=group, user_id=user_id).delete()
        return Response({"detail": "User removed."}, status=204)


class SendGroupMessageView(generics.CreateAPIView):
    """
    Send a message to a group you belong to.
    """
    serializer_class = GroupMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Send group message")
    def perform_create(self, serializer):
        group = serializer.validated_data["group"]
        if not GroupMembership.objects.filter(group=group, user=self.request.user).exists():
            raise PermissionDenied("You are not a member of this group.")
        serializer.save(sender=self.request.user)


class GroupMessagesView(generics.ListAPIView):
    """
    View messages from a group you belong to.
    """
    serializer_class = GroupMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination

    @swagger_auto_schema(operation_summary="View group messages (paginated)")
    def get_queryset(self):
        group_id = self.kwargs["group_id"]
        group = Group.objects.get(id=group_id)

        if not GroupMembership.objects.filter(group=group, user=self.request.user).exists():
            raise PermissionDenied("You are not a member of this group.")

        return group.messages.all().order_by("-created_at")
    

class SearchGroupsView(APIView):
    """
    Search for groups by name or description (includes all groups, whether you're a member or not).
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination

    @swagger_auto_schema(
        operation_summary="Search all groups",
        manual_parameters=[
            openapi.Parameter(
                'q', openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description="Keyword for group name/description",
            )
        ],
    )
    def get(self, request):
        query = request.GET.get("q", "").strip()
        if not query:
            return Response({"error": "Query parameter `q` is required."}, status=400)

        groups = Group.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by("name")

        paginator = self.pagination_class()
        paginated = paginator.paginate_queryset(groups, request)
        serializer = GroupSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)


class JoinGroupView(APIView):
    """
    Join a group by ID (if not already a member).
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Join group by ID")
    def post(self, request, group_id):
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return Response({"error": "Group not found"}, status=404)

        membership, created = GroupMembership.objects.get_or_create(group=group, user=request.user)
        if created:
            return Response({"detail": f"You joined '{group.name}'"}, status=200)
        return Response({"detail": "Already a member"}, status=200)
