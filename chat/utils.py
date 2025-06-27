from chat.models import UserProfile, FriendRequest

def get_friends(user):
    sent = FriendRequest.objects.filter(from_user=user, status='accepted').values_list('to_user', flat=True)
    received = FriendRequest.objects.filter(to_user=user, status='accepted').values_list('from_user', flat=True)
    friend_ids = set(sent).union(set(received))
    return UserProfile.objects.filter(user__id__in=friend_ids).order_by("id")


def are_friends(user1, user2):
    return FriendRequest.objects.filter(
        from_user=user1,
        to_user=user2,
        status='accepted'
    ).exists() or FriendRequest.objects.filter(
        from_user=user2,
        to_user=user1,
        status='accepted'
    ).exists()


def get_friend_ids(user):
    sent = FriendRequest.objects.filter(from_user=user, status='accepted').values_list('to_user', flat=True)
    received = FriendRequest.objects.filter(to_user=user, status='accepted').values_list('from_user', flat=True)
    return list(set(sent).union(set(received)))
