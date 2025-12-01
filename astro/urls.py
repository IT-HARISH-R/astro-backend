from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("data/",include("prediction.urls")),
    path("ai/",include("ai.urls")),
    path('bot/', include('bot.urls')),
    path('plans/', include('plans.urls')),
    path("zodiac/", include("zodiac.urls")),
    path("voice/", include("user_prediction.urls")), 
    path("future/", include("future_predictions.urls")), 
    path("api/dashboard/", include("dashboard.urls")) ,
    path('api/subscriptions/', include('subscriptions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)