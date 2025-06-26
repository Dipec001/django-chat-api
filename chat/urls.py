from django.urls import path
from chat.views.user_views import (RegisterView, UserProfileView)
from chat.views.friend_views import (SendFriendRequestView, AcceptFriendRequestView,
                                    DeclineFriendRequestView, RemoveFriendView, FriendListView,
                                      PendingFriendRequestsView, SearchUsersView)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('friends/request/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friends/accept/<int:pk>/', AcceptFriendRequestView.as_view(), name='accept-friend-request'),
    path('friends/decline/<int:pk>/', DeclineFriendRequestView.as_view(), name='decline-friend-request'),
    path('friends/remove/', RemoveFriendView.as_view(), name='remove-friend'),
    path('friends/', FriendListView.as_view(), name='friend-list'),
    path('friends/pending/', PendingFriendRequestsView.as_view(), name='pending-friend-requests'),
    path('users/search/', SearchUsersView.as_view(), name='user-search'),

]
