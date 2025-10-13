from django.urls import path
from .views import RegisterView, ProfileView, UserListView , UpdateProfileView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/update/", UpdateProfileView.as_view(), name="update-profile"),
    path("users/", UserListView.as_view(), name="users"),  # 🔥 only admin can access

]

