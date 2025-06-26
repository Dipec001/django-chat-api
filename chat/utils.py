from chat.models import UserProfile, FriendRequest

def get_friends(user):
    sent = FriendRequest.objects.filter(from_user=user, status='accepted').values_list('to_user', flat=True)
    received = FriendRequest.objects.filter(to_user=user, status='accepted').values_list('from_user', flat=True)
    friend_ids = set(sent).union(set(received))
    return UserProfile.objects.filter(user__id__in=friend_ids).order_by("id")
