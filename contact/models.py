from django.db import models
from django.conf import settings
from django.utils import timezone  # Add this import

class Contact(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('replied', 'Replied'),
        ('archived', 'Archived'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts"
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # New fields for status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    replied_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.subject} ({self.status})"

    def save(self, *args, **kwargs):
        # Auto update timestamps for status changes
        if self.pk:  
            try:
                old = Contact.objects.get(pk=self.pk)
                if old.status != self.status:
                    if self.status == 'replied' and not self.replied_at:
                        self.replied_at = timezone.now()
                    elif self.status == 'archived' and not self.archived_at:
                        self.archived_at = timezone.now()
            except Contact.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)