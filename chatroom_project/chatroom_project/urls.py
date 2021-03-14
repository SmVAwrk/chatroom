from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from chatroom_project import settings

urlpatterns = [
    path('admin/', admin.site.urls),

    # Djoser auth
    path('api/v1/auth/', include('djoser.urls')),
    path('api/v1/auth/', include('djoser.urls.authtoken')),
    path('api/v1/auth/', include('djoser.urls.jwt')),

    # Social auth
    path('api/v1/oauth/', include('rest_framework_social_oauth2.urls')),

    # Profile app
    path('api/v1/', include('user_profile.urls')),

    # Chat app
    path('api/v1/chat/', include('chat_app.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Подключение Debug toolbar
if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
