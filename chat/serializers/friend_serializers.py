from rest_framework import serializers
from chat.models import FriendRequest, UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()

class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = serializers.StringRelatedField(read_only=True)
    to_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'status', 'created_at', 'updated_at']
        read_only_fields = ['status']


class UserSearchResultSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user_id', 'username', 'full_name', 'avatar_url']