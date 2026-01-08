from django.urls import path
from .views import ContactView, ContactDetailView, ContactReplyView

urlpatterns = [
    path('ask/', ContactView.as_view(), name='contact-list'),
    path('ask/<int:pk>/', ContactDetailView.as_view(), name='contact-detail'),
    path('ask/<int:pk>/reply/', ContactReplyView.as_view(), name='contact-reply'), 
]