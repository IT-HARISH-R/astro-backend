from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GenerateTextSerializer
from rest_framework.permissions import AllowAny
# official google genai SDK
import google.generativeai as genai


class GenerateTextAPIView(APIView):
    """
    POST { "prompt": "Hello, how are you?", "model": "gemini-2.5-flash" }
    returns { "output": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        print(request.data)
        serializer = GenerateTextSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        prompt = serializer.validated_data["prompt"]
        model = serializer.validated_data.get("model") or "gemini-2.5-flash"

        try:
            # Initialize client with API key from settings/env
            client = genai.Client(api_key="AIzaSyBHxU-sHljwDG-w4MDgPH9o6U1XRBgrV64")

            # Use models.generate_content as in Google docs
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            # SDK returns structured response; many examples use response.text or response["candidates"]
            # We'll try to fetch a textual candidate safely:
            text_output = None
            if hasattr(response, "text"):
                text_output = response.text
            else:
                # safe fallback: try to extract from response dict-like structure
                try:
                    # many SDK responses have 'candidates' list with 'content' or 'output'
                    cand = response.get("candidates", [])
                    if cand and isinstance(cand, list):
                        # prefer 'content' or 'output' fields if exist
                        text_output = cand[0].get("content") or cand[0].get("output") or str(cand[0])
                except Exception:
                    text_output = str(response)

            return Response({"output": text_output}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
