from django.contrib import admin
from django.urls import path, include

from chat_app.views import AuthView
from chatroom_project.settings import DEBUG

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', AuthView.as_view()),

    # Djoser auth
    path('api/v1/auth/', include('djoser.urls')),
    path('api/v1/auth/', include('djoser.urls.authtoken')),
    path('api/v1/auth/', include('djoser.urls.jwt')),

    # Social auth
    path('api/v1/oauth/', include('rest_framework_social_oauth2.urls')),
]

# Подключение Debug toolbar
if DEBUG:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
