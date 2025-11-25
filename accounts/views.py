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
    parser_classes = (MultiPartParser, FormParser)

    def put(self, request):
        user = request.user
        # print("FILES:", request.FILES)
        # print("DATA:", request.data)
        data = {}

        # Copy non-file fields, explicitly exclude profile_image
        for field in ["username","language","birth_place", "first_name", "last_name", "birth_year", "birth_month", "birth_day", "birth_hour", "birth_minute"]:
            if field in request.data: 
                data[field] = request.data[field]
 
        # Handle profile image from request.FILES only
        profile_file = request.FILES.get("profile_image")
        if profile_file:
            try:
                # Validate file type
                if not profile_file.content_type.startswith("image/"):
                    return Response(
                        {"detail": "Only image files are allowed."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                upload_result = cloudinary.uploader.upload(
                    profile_file,
                    folder="profile_images",
                    public_id=f"user_{user.id}",
                    overwrite=True,
                )
                data["profile_image"] = upload_result["secure_url"]
            except Exception as e:
                return Response(
                    {"detail": f"Failed to upload profile image: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = UserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "detail": "Profile updated successfully",
                "user": serializer.data
            })
        print("Serializer errors:", serializer.errors)  # Debug serializer errors
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
