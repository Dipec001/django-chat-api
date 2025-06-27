from rest_framework import serializers
from chat.models import Message
from django.contrib.auth import get_user_model

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)
    receiver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    receiver_username = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'receiver_username', 'content', 'message_type', 'is_read', 'created_at']
        read_only_fields = ['is_read']

    def get_receiver_username(self, obj):
        return obj.receiver.profile.username if hasattr(obj.receiver, "profile") else None

