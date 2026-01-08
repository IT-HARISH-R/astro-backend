from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q 
from django.utils import timezone
from .models import Contact
from .serializers import ContactSerializer
from email_utils.email_services import EmailService 

class ContactView(APIView):
    # GET: AllowAny (for admin panel access)
    # POST: AllowAny (anyone can submit)
    # PATCH, DELETE: IsAuthenticated (only admin can modify)
    
    def get_permissions(self):
        if self.request.method in ['GET', 'POST']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    # GET all inquiries (with optional query parameters)
    def get(self, request):
        try:
            # Get query parameters
            status_filter = request.query_params.get('status', None)
            search = request.query_params.get('search', None)
            
            contacts = Contact.objects.all().order_by('-created_at')
            
            # Apply filters if provided
            if status_filter and status_filter != 'all':
                contacts = contacts.filter(status=status_filter)
            
            if search:
                contacts = contacts.filter(
                    Q(name__icontains=search) |
                    Q(email__icontains=search) |
                    Q(subject__icontains=search) |
                    Q(message__icontains=search)
                )
            
            serializer = ContactSerializer(contacts, many=True)
            
            # Get stats
            total = Contact.objects.count()
            new_count = Contact.objects.filter(status='new').count()
            replied_count = Contact.objects.filter(status='replied').count()
            archived_count = Contact.objects.filter(status='archived').count()
            
            return Response({
                'data': serializer.data,
                'stats': {
                    'total': total,
                    'new': new_count,
                    'replied': replied_count,
                    'archived': archived_count
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # POST new inquiry (public access)
    def post(self, request):
        try:
            data = request.data.copy()
            
            # Check if user is authenticated
            user = None
            if request.user.is_authenticated:
                user = request.user
            
            serializer = ContactSerializer(data=data)
            if serializer.is_valid():
                contact = serializer.save(user=user if user else None)
                
                response_data = serializer.data
                response_data['message'] = 'Contact message sent successfully'
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContactDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # GET single inquiry
    def get(self, request, pk):
        try:
            contact = get_object_or_404(Contact, pk=pk)
            serializer = ContactSerializer(contact)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # PATCH update inquiry (status, etc.)
    def patch(self, request, pk):
        try:
            contact = get_object_or_404(Contact, pk=pk)
            
            # Only allow status update for now
            allowed_fields = ['status']
            data = {key: request.data[key] for key in allowed_fields if key in request.data}
            
            serializer = ContactSerializer(contact, data=data, partial=True)
            if serializer.is_valid():
                updated_contact = serializer.save()
                
                # Auto-update timestamps based on status
                if 'status' in data:
                    if data['status'] == 'replied' and not contact.replied_at:
                        updated_contact.replied_at = timezone.now()
                        updated_contact.save(update_fields=['replied_at'])
                    elif data['status'] == 'archived' and not contact.archived_at:
                        updated_contact.archived_at = timezone.now()
                        updated_contact.save(update_fields=['archived_at'])
                
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # DELETE inquiry
    def delete(self, request, pk):
        try:
            contact = get_object_or_404(Contact, pk=pk)
            contact.delete()
            return Response(
                {'message': 'Contact inquiry deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        





class ContactDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # GET single inquiry
    def get(self, request, pk):
        try:
            contact = get_object_or_404(Contact, pk=pk)
            serializer = ContactSerializer(contact)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # PATCH update inquiry (status, etc.)
    def patch(self, request, pk):
        try:
            contact = get_object_or_404(Contact, pk=pk)
            
            # Check if we're sending a reply
            reply_message = request.data.get('reply_message', None)
            email_subject = request.data.get('email_subject', None)
            
            # Update status
            allowed_fields = ['status']
            data = {key: request.data[key] for key in allowed_fields if key in request.data}
            
            serializer = ContactSerializer(contact, data=data, partial=True)
            if serializer.is_valid():
                updated_contact = serializer.save()
                
                # Auto-update timestamps based on status
                if 'status' in data:
                    if data['status'] == 'replied' and not contact.replied_at:
                        updated_contact.replied_at = timezone.now()
                        updated_contact.save(update_fields=['replied_at'])
                    elif data['status'] == 'archived' and not contact.archived_at:
                        updated_contact.archived_at = timezone.now()
                        updated_contact.save(update_fields=['archived_at'])
                
                # Send email if reply message is provided
                if reply_message:
                    success, message = EmailService.send_contact_reply_email(
                        inquiry=contact,
                        reply_message=reply_message,
                        subject=email_subject or f"Re: {contact.subject}"
                    )
                    
                    if not success:
                        return Response(
                            {'error': f'Status updated but email failed: {message}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                
                return Response({
                    'message': 'Status updated successfully' + (' and email sent' if reply_message else ''),
                    'data': serializer.data
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # DELETE inquiry
    def delete(self, request, pk):
        try:
            contact = get_object_or_404(Contact, pk=pk)
            contact.delete()
            return Response(
                {'message': 'Contact inquiry deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Add new endpoint for sending reply
class ContactReplyView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            contact = get_object_or_404(Contact, pk=pk)
            
            # Get email data from request
            reply_message = request.data.get('message', '')
            email_subject = request.data.get('subject', f"Re: {contact.subject}")
            
            if not reply_message:
                return Response(
                    {'error': 'Reply message is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Send email
            success, message = EmailService.send_contact_reply_email(
                inquiry=contact,
                reply_message=reply_message,
                subject=email_subject
            )
            
            if success:
                # Update contact status to replied
                contact.status = 'replied'
                contact.replied_at = timezone.now()
                contact.save()
                
                return Response({
                    'success': True,
                    'message': 'Reply email sent successfully',
                    'data': ContactSerializer(contact).data
                })
            else:
                return Response(
                    {'error': f'Failed to send email: {message}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )