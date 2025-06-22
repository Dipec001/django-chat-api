from django.urls import path
from chat.views.user_views import RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
]
