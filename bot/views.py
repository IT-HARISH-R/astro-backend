from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
import json
from django.conf import settings
from rest_framework.permissions import AllowAny

# Set your WhatsApp Cloud API token and phone ID
WHATSAPP_TOKEN = settings.WHATSAPP_TOKEN
PHONE_NUMBER_ID = settings.PHONE_NUMBER_ID

class WhatsAppWebhookView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Webhook verification"""
        verify_token = settings.VERIFY_TOKEN
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge') 

        if mode == 'subscribe' and token == verify_token:
            return Response(challenge, status=status.HTTP_200_OK)
        return Response('Verification failed', status=status.HTTP_403_FORBIDDEN)

    def post(self, request, *args, **kwargs): 
        """Handle incoming WhatsApp messages""" 
        data = request.data
        print("Incoming webhook:", json.dumps(data, indent=2))

        try:
            messages = data['entry'][0]['changes'][0]['value'].get('messages', [])
            for msg in messages:
                from_number = msg.get('from')
                msg_text = msg.get('text', {}).get('body', '')

                if from_number and msg_text:
                    reply_text = f"Hello! You said: {msg_text}"
                    self.send_message(from_number, reply_text)

        except (KeyError, IndexError) as e:
            print("Webhook parse error:", str(e))

        return Response(status=status.HTTP_200_OK)

    def send_message(self, to_number, message):
        """Send message via WhatsApp Cloud API"""
        url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "text": {"body": message}
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            print("Send message response:", json.dumps(response_data, indent=2))

            if response.status_code != 200:
                print("❌ Error sending message:", response_data)
                

        except requests.RequestException as e:
            print("⚠️ Request error:", str(e))
