from rest_framework import serializers
from chat.models import Group, GroupMembership, GroupMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class GroupSerializer(serializers.ModelSerializer):
    creator = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'creator', 'image_url', 'created_at', 'updated_at']

class GroupMembershipSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = GroupMembership
        fields = ['id', 'group', 'user', 'joined_at']

class GroupMessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())

    class Meta:
        model = GroupMessage
        fields = ['id', 'group', 'sender', 'content', 'message_type', 'is_read', 'created_at']
        read_only_fields = ['is_read']
