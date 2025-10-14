from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, UserSerializer
from .models import User
import cloudinary.uploader
from rest_framework.parsers import MultiPartParser, FormParser

# --- Register User ---
class RegisterView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

# --- Get Profile ---
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

# --- Update Profile ---
class UpdateProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # <--- This is required

    def put(self, request):
        user = request.user
        data = request.data.copy()

        # ✅ Handle profile image upload to Cloudinary
        if "profile_image" in request.FILES:
            image = request.FILES["profile_image"]
            upload_result = cloudinary.uploader.upload(
                image,
                folder="profile_images",  # optional folder in Cloudinary
                public_id=f"user_{user.id}",  # optional custom id
                overwrite=True,
            )
            data["profile_image"] = upload_result["secure_url"]  # save URL in DB

        serializer = UserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "detail": "Profile updated successfully",
                "user": serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- User List (Admin Only) ---
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        if not request.user.is_admin():  # check role
            return Response({"detail": "You are not allowed to view this data"}, status=403)
        return super().list(request, *args, **kwargs)
