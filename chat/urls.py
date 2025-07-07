from django.urls import path, include
from chat.views.user_views import (RegisterView, UserProfileView)
from chat.views.friend_views import (SendFriendRequestView, AcceptFriendRequestView,
                                    DeclineFriendRequestView, RemoveFriendView, FriendListView,
                                      PendingFriendRequestsView, SearchUsersView)
from chat.views.message_views import (SendMessageView, ChatInboxView, ChatHistoryView)
from chat.views.group_views import (
    GroupViewSet, AddGroupMemberView, RemoveGroupMemberView,
    SendGroupMessageView, GroupMessagesView,
    SearchGroupsView, JoinGroupView
)
from rest_framework.routers import DefaultRouter
from chat.health import health_check


router = DefaultRouter()
router.register(r'groups', GroupViewSet, basename='group')

urlpatterns = [
    # Health Check
    path('health/', health_check, name='health_check'),

    # User Views
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # Friends
    path('friends/request/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friends/accept/<int:pk>/', AcceptFriendRequestView.as_view(), name='accept-friend-request'),
    path('friends/decline/<int:pk>/', DeclineFriendRequestView.as_view(), name='decline-friend-request'),
    path('friends/remove/', RemoveFriendView.as_view(), name='remove-friend'),
    path('friends/', FriendListView.as_view(), name='friend-list'),
    path('friends/pending/', PendingFriendRequestsView.as_view(), name='pending-friend-requests'),

    # User Search
    path('users/search/', SearchUsersView.as_view(), name='user-search'),

    # One-on-one messaging
    path('messages/send/', SendMessageView.as_view(), name='send-message'),
    path('messages/user/<int:id>/', ChatHistoryView.as_view(), name='chat-history'),
    path('messages/inbox/', ChatInboxView.as_view(), name='chat-inbox'),

    # Group actions outside of ViewSet
    path('groups/<int:group_id>/add-member/', AddGroupMemberView.as_view(), name='add-group-member'),
    path('groups/<int:group_id>/remove-member/<int:user_id>/', RemoveGroupMemberView.as_view(), name='remove-group-member'),
    path('groups/messages/send/', SendGroupMessageView.as_view(), name='send-group-message'),
    path('groups/<int:group_id>/messages/', GroupMessagesView.as_view(), name='group-messages'),
    path('groups/search/', SearchGroupsView.as_view(), name='search-group'),
    path('groups/<int:group_id>/join/', JoinGroupView.as_view(), name='join-group'),

    path('', include(router.urls)),
]