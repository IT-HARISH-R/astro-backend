from django.utils.deprecation import MiddlewareMixin
import datetime

class LogRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Request path & time log pannuthu
        print(f"[{datetime.datetime.now()}] Request path: {request.path} Method: {request.method}")
        # You can also add custom logic, e.g., auth check
        return None

    def process_response(self, request, response):
        print(f"[{datetime.datetime.now()}] Response status: {response.status_code}")
        return response
