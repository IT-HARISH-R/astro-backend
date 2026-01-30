from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

class EmailService:
    
    @staticmethod
    def send_contact_reply_email(inquiry, reply_message, subject=None):
        """
        Send email reply to contact inquiry
        
        Args:
            inquiry: Contact model instance
            reply_message: Reply message content
            subject: Email subject (optional)
        """
        try:
            context = {
                'inquiry': inquiry,
                'reply_message': reply_message,
                'reply_date': timezone.now(),
                'site_name': 'AstroVerse',
                'support_email': 'support@astroverse.com'
            }
            
            # Use custom subject or default
            email_subject = subject or f"Re: {inquiry.subject}"
            
            # Debug: Print template search paths
            from django.template.loader import get_template
            try:
                template = get_template('emails/contact_reply.html')  # Wrong
                # template = get_template('email_utils/contact_reply.html') //correct
                print(f"Template found: {template.origin}")
            except Exception as e:
                print(f"Template error: {e}")
                # Create a fallback HTML
                html_message = EmailService._create_fallback_html(inquiry, reply_message, context)
            else:
                # Render HTML template
                html_message = render_to_string('emails/contact_reply.html', context) # Wrong
                # html_message = render_to_string('email_utils/contact_reply.html', context) //correct
            
            # Create email
            email = EmailMessage(
                subject=email_subject,
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[inquiry.email],
                reply_to=[settings.DEFAULT_FROM_EMAIL]
            )
            
            # Set content type to HTML
            email.content_subtype = 'html'
            
            # Send email
            email.send(fail_silently=False)  # Set fail_silently to False to see errors
            
            return True, "Email sent successfully"
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            # Try to send a simple text email as fallback
            try:
                EmailService._send_fallback_email(inquiry, reply_message, email_subject)
                return True, "Email sent (fallback method)"
            except Exception as fallback_error:
                print(f"Fallback also failed: {str(fallback_error)}")
                return False, str(e)
    
    @staticmethod
    def _create_fallback_html(inquiry, reply_message, context):
        """Create a simple HTML fallback if template is missing"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background: #667eea; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .original {{ background: #f3f4f6; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0; }}
                .reply {{ background: #d1fae5; padding: 15px; border-left: 4px solid #10b981; margin: 20px 0; }}
                .footer {{ background: #f9fafb; padding: 15px; text-align: center; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Astro Support</h1>
            </div>
            <div class="content">
                <p>Dear {inquiry.name},</p>
                <p>Thank you for contacting Astro. Here is our response to your inquiry:</p>
                
                <div class="original">
                    <strong>Your Original Message:</strong>
                    <p>{inquiry.message}</p>
                </div>
                
                <div class="reply">
                    <strong>Our Response:</strong>
                    <p>{reply_message}</p>
                </div>
                
                <p>Best regards,<br>The Astro Team</p>
            </div>
            <div class="footer">
                <p>&copy; {context['reply_date'].year} Astro</p>
                <p>Reference: #{inquiry.id}</p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def _send_fallback_email(inquiry, reply_message, subject):
        """Send a simple text email as fallback"""
        text_content = f"""
        Dear {inquiry.name},
        
        Thank you for contacting Astro. Here is our response:
        
        Your original message:
        {inquiry.message}
        
        Our reply:
        {reply_message}
        
        Best regards,
        The Astro Team
        
        Reference ID: #{inquiry.id}
        """
        
        email = EmailMessage(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[inquiry.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        email.send()
    
