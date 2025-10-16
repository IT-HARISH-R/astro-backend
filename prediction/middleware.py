import jwt
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()

class AccessTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        print("hi")
        auth = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION", "")
        print(auth)
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1].strip()
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                request.user_payload = payload

                # Get user_id from payload
                user_id = payload.get("user_id")
                if user_id:
                    try:
                        user = User.objects.get(id=user_id)
                        request.user = user  
                        request.username = user.username
                        request.user_id = user.id
                    except User.DoesNotExist:
                        return JsonResponse({"error": "User not found"}, status=401)
                else:
                    return JsonResponse({"error": "Invalid token: no user_id"}, status=401)

            except jwt.InvalidTokenError:
                return JsonResponse({"error": "Invalid token"}, status=401)
        else:
            request.user_payload = None
            request.user = None
            request.username = None
            request.user_id = None
